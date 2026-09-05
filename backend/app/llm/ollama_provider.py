import json
import time
from typing import Any, AsyncIterator, Dict, List, Optional
import httpx

from backend.app.config import settings
from backend.app.llm.base import BaseLLMProvider, LLMResponse


class OllamaProvider(BaseLLMProvider):
    """Local Ollama Provider for offline and local-first execution."""

    def __init__(self, model: str = "llama3.1:8b", base_url: Optional[str] = None):
        super().__init__(model=model)
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")

    async def is_available(self) -> bool:
        """Check if local Ollama daemon is reachable."""
        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    async def get_installed_models(self) -> List[str]:
        """Fetch list of locally downloaded models from Ollama."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    return [m.get("name", "") for m in data.get("models", [])]
        except Exception:
            pass
        return []


    def _prepare_messages(self, messages: List[Dict[str, str]], system: Optional[str] = None) -> List[Dict[str, str]]:
        formatted = []
        if system:
            formatted.append({"role": "system", "content": system})
        for m in messages:
            formatted.append({"role": m["role"], "content": m["content"]})
        return formatted

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": self._prepare_messages(messages, system),
            "stream": False,
        }
        if response_format and response_format.get("type") == "json_object":
            payload["format"] = "json"

        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, json=payload)
                latency_ms = (time.perf_counter() - start_time) * 1000

                if resp.status_code != 200:
                    raise RuntimeError(f"Ollama API error {resp.status_code}: {resp.text}")

                data = resp.json()
        except httpx.ConnectError:
            raise RuntimeError(f"Cannot connect to local Ollama at {self.base_url}. Is Ollama running?")

        content = data.get("message", {}).get("content", "")
        usage = {
            "prompt_eval_count": data.get("prompt_eval_count", 0),
            "eval_count": data.get("eval_count", 0),
        }

        return LLMResponse(
            text=content,
            tool_calls=[],
            usage=usage,
            latency_ms=round(latency_ms, 2),
            provider="ollama",
            model=self.model,
        )

    async def stream(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
    ) -> AsyncIterator[str]:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": self._prepare_messages(messages, system),
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    err = await response.aread()
                    raise RuntimeError(f"Ollama streaming error {response.status_code}: {err.decode()}")

                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            chunk = json.loads(line)
                            delta = chunk.get("message", {}).get("content", "")
                            if delta:
                                yield delta
                        except Exception:
                            continue
