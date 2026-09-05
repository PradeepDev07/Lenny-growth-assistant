import json
import time
from typing import Any, AsyncIterator, Dict, List, Optional
import httpx

from backend.app.config import settings
from backend.app.llm.base import BaseLLMProvider, LLMResponse


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter Provider for unified access to Claude, GPT-4o, Llama, etc."""

    def __init__(self, model: str = "anthropic/claude-3.7-sonnet", api_key: Optional[str] = None):
        super().__init__(model=model)
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    async def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 0)

    def _prepare_messages(self, messages: List[Dict[str, str]], system: Optional[str] = None) -> List[Dict[str, str]]:
        formatted = []
        if system:
            formatted.append({"role": "system", "content": system})
        formatted.extend(messages)
        return formatted

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        if not await self.is_available():
            raise ValueError("OPENROUTER_API_KEY is not configured.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://lennygrowthassistant.local",
            "X-Title": "Lenny Growth Assistant",
            "Content-Type": "application/json",
        }

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": self._prepare_messages(messages, system),
        }
        if response_format:
            payload["response_format"] = response_format

        start_time = time.perf_counter()
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(self.base_url, headers=headers, json=payload)
            latency_ms = (time.perf_counter() - start_time) * 1000

            if resp.status_code != 200:
                raise RuntimeError(f"OpenRouter API error {resp.status_code}: {resp.text}")

            data = resp.json()

        choice = data.get("choices", [{}])[0]
        text = choice.get("message", {}).get("content", "")
        usage = data.get("usage", {})

        return LLMResponse(
            text=text,
            tool_calls=[],
            usage=usage,
            latency_ms=round(latency_ms, 2),
            provider="openrouter",
            model=self.model,
        )

    async def stream(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
    ) -> AsyncIterator[str]:
        if not await self.is_available():
            raise ValueError("OPENROUTER_API_KEY is not configured.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://lennygrowthassistant.local",
            "X-Title": "Lenny Growth Assistant",
            "Content-Type": "application/json",
        }

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": self._prepare_messages(messages, system),
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=90.0) as client:
            async with client.stream("POST", self.base_url, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    err = await response.aread()
                    raise RuntimeError(f"OpenRouter streaming error {response.status_code}: {err.decode()}")

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content")
                            if content:
                                yield content
                        except Exception:
                            continue
