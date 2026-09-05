import logging
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

from backend.app.config import settings
from backend.app.llm.base import BaseLLMProvider, LLMResponse
from backend.app.llm.gemini_provider import GeminiProvider
from backend.app.llm.openrouter_provider import OpenRouterProvider
from backend.app.llm.ollama_provider import OllamaProvider

logger = logging.getLogger("model_router")


class ModelRouter:
    """Task-based dynamic model router with automated fallback chains."""

    DEFAULT_CHAINS: Dict[str, List[Tuple[str, str]]] = {
        "retrieval_qa": [
            ("gemini", settings.MODEL_FOR_RETRIEVAL_QA),
            ("openrouter", settings.MODEL_FOR_ESSAY),
            ("ollama", settings.MODEL_FOR_OFFLINE),
        ],
        "essay_generation": [
            ("openrouter", settings.MODEL_FOR_ESSAY),
            ("gemini", settings.MODEL_FOR_RETRIEVAL_QA),
            ("ollama", settings.MODEL_FOR_OFFLINE),
        ],
        "artifact_generation": [
            ("gemini", settings.MODEL_FOR_ARTIFACT),
            ("openrouter", settings.MODEL_FOR_ESSAY),
            ("ollama", settings.MODEL_FOR_OFFLINE),
        ],
        "intent_routing": [
            ("gemini", settings.MODEL_FOR_INTENT_ROUTING),
            ("ollama", settings.MODEL_FOR_OFFLINE),
        ],
        "offline_demo_mode": [
            ("ollama", settings.MODEL_FOR_OFFLINE),
        ],
    }

    def __init__(self):
        # Runtime overrides table
        self.task_overrides: Dict[str, Tuple[str, str]] = {}
        self.routing_audit_logs: List[Dict[str, Any]] = []

    def get_provider_instance(self, provider_name: str, model_id: str) -> BaseLLMProvider:
        """Instantiate provider by name."""
        provider_name = provider_name.lower().strip()
        if provider_name == "gemini":
            return GeminiProvider(model=model_id)
        elif provider_name == "openrouter":
            return OpenRouterProvider(model=model_id)
        elif provider_name == "ollama":
            return OllamaProvider(model=model_id)
        else:
            raise ValueError(f"Unknown provider '{provider_name}'")

    def get_chain_for_task(self, task: str) -> List[Tuple[str, str]]:
        """Return the prioritized list of (provider, model) pairs for a task."""
        chain = list(self.DEFAULT_CHAINS.get(task, [("gemini", settings.MODEL_FOR_RETRIEVAL_QA), ("ollama", settings.MODEL_FOR_OFFLINE)]))
        if task in self.task_overrides:
            override = self.task_overrides[task]
            # Place override at the head of the chain if not already there
            chain = [override] + [item for item in chain if item != override]
        return chain

    def set_task_override(self, task: str, provider: str, model: str):
        """Set a runtime override for a task."""
        self.task_overrides[task] = (provider.lower().strip(), model.strip())
        logger.info(f"Updated task override: task={task} -> {provider}/{model}")

    async def check_provider_connectivity(self) -> Dict[str, Dict[str, Any]]:
        """Probe reachability for all configured providers."""
        gemini = GeminiProvider()
        openrouter = OpenRouterProvider()
        ollama = OllamaProvider()

        ollama_running = await ollama.is_available()
        installed_models = await ollama.get_installed_models() if ollama_running else []
        default_model = settings.MODEL_FOR_OFFLINE
        has_default_model = any(default_model in m for m in installed_models)

        return {
            "gemini": {
                "configured": await gemini.is_available(),
                "default_model": settings.MODEL_FOR_RETRIEVAL_QA,
            },
            "openrouter": {
                "configured": await openrouter.is_available(),
                "default_model": settings.MODEL_FOR_ESSAY,
            },
            "ollama": {
                "configured": ollama_running and (len(installed_models) > 0),
                "is_running": ollama_running,
                "installed_models": installed_models,
                "has_default_model": has_default_model,
                "default_model": default_model,
                "endpoint": settings.OLLAMA_BASE_URL,
            },
        }


    def get_current_routes(self) -> Dict[str, Dict[str, Any]]:
        """Return current effective primary model for each task."""
        result = {}
        for task in self.DEFAULT_CHAINS.keys():
            chain = self.get_chain_for_task(task)
            primary_provider, primary_model = chain[0]
            result[task] = {
                "provider": primary_provider,
                "model": primary_model,
                "fallback_chain": [{"provider": p, "model": m} for p, m in chain[1:]],
                "is_overridden": task in self.task_overrides,
            }
        return result

    async def generate_for_task(
        self,
        task: str,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Tuple[LLMResponse, Dict[str, Any]]:
        """Execute generation iterating down fallback chain if errors occur."""
        chain = self.get_chain_for_task(task)
        errors = []

        primary_provider, primary_model = chain[0]

        for idx, (provider_name, model_id) in enumerate(chain):
            is_fallback = idx > 0
            try:
                provider = self.get_provider_instance(provider_name, model_id)
                if not await provider.is_available():
                    errors.append(f"{provider_name}: provider not configured or unavailable")
                    continue

                response = await provider.generate(
                    messages=messages,
                    system=system,
                    tools=tools,
                    response_format=response_format,
                )

                routing_meta = {
                    "task": task,
                    "provider": response.provider,
                    "model": response.model,
                    "fallback_used": is_fallback,
                    "fallback_from": primary_provider if is_fallback else None,
                    "latency_ms": response.latency_ms,
                }
                self.routing_audit_logs.append(routing_meta)
                return response, routing_meta

            except Exception as e:
                logger.warning(f"Error calling {provider_name}/{model_id} for task '{task}': {e}")
                errors.append(f"{provider_name}/{model_id}: {str(e)}")

        raise RuntimeError(
            f"All providers in fallback chain failed for task '{task}'. Chain: {chain}. Errors: {errors}"
        )

    async def get_active_provider_for_stream(self, task: str) -> Tuple[BaseLLMProvider, Dict[str, Any]]:
        """Select the first reachable provider in chain for streaming."""
        chain = self.get_chain_for_task(task)
        primary_provider, primary_model = chain[0]

        for idx, (provider_name, model_id) in enumerate(chain):
            is_fallback = idx > 0
            provider = self.get_provider_instance(provider_name, model_id)
            if await provider.is_available():
                meta = {
                    "task": task,
                    "provider": provider_name,
                    "model": model_id,
                    "fallback_used": is_fallback,
                    "fallback_from": primary_provider if is_fallback else None,
                }
                return provider, meta

        # Fallback to local Ollama instance anyway
        ollama = OllamaProvider(model=settings.MODEL_FOR_OFFLINE)
        return ollama, {
            "task": task,
            "provider": "ollama",
            "model": settings.MODEL_FOR_OFFLINE,
            "fallback_used": True,
            "fallback_from": primary_provider,
        }


# Global router singleton
model_router = ModelRouter()
