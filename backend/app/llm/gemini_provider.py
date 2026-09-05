import json
import time
from typing import Any, AsyncIterator, Dict, List, Optional
import httpx

from backend.app.config import settings
from backend.app.llm.base import BaseLLMProvider, LLMResponse


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider using direct Google Generative AI REST API."""

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        super().__init__(model=model or settings.MODEL_FOR_RETRIEVAL_QA)
        self.api_key = settings.GEMINI_API_KEY if api_key is None else api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 0)

    def _convert_messages(self, messages: List[Dict[str, str]], system: Optional[str] = None) -> Dict[str, Any]:
        contents = []
        for msg in messages:
            role = "user" if msg["role"] in ("user", "system") else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}],
            })

        payload: Dict[str, Any] = {"contents": contents}
        if system:
            payload["systemInstruction"] = {
                "parts": [{"text": system}]
            }
        return payload

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        if not await self.is_available():
            raise ValueError("GEMINI_API_KEY is not configured.")

        # Normalize model name
        model_id = self.model
        if not model_id.startswith("models/"):
            model_id = f"models/{model_id}"

        url = f"{self.base_url}/{model_id}:generateContent?key={self.api_key}"
        payload = self._convert_messages(messages, system)

        start_time = time.perf_counter()
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, json=payload)
            latency_ms = (time.perf_counter() - start_time) * 1000

            if resp.status_code != 200:
                raise RuntimeError(f"Gemini API error {resp.status_code}: {resp.text}")

            data = resp.json()

        text_parts = []
        try:
            candidates = data.get("candidates", [])
            if candidates:
                for part in candidates[0].get("content", {}).get("parts", []):
                    if "text" in part:
                        text_parts.append(part["text"])
        except Exception as e:
            raise RuntimeError(f"Failed to parse Gemini response: {e}")

        usage = data.get("usageMetadata", {})

        return LLMResponse(
            text="".join(text_parts),
            tool_calls=[],
            usage=usage,
            latency_ms=round(latency_ms, 2),
            provider="gemini",
            model=self.model,
        )

    async def stream(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
    ) -> AsyncIterator[str]:
        if not await self.is_available():
            raise ValueError("GEMINI_API_KEY is not configured.")

        model_id = self.model
        if not model_id.startswith("models/"):
            model_id = f"models/{model_id}"

        url = f"{self.base_url}/{model_id}:streamGenerateContent?alt=sse&key={self.api_key}"
        payload = self._convert_messages(messages, system)

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    err_content = await response.aread()
                    raise RuntimeError(f"Gemini streaming error {response.status_code}: {err_content.decode()}")

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str:
                            try:
                                chunk_data = json.loads(data_str)
                                candidates = chunk_data.get("candidates", [])
                                if candidates:
                                    for part in candidates[0].get("content", {}).get("parts", []):
                                        if "text" in part:
                                            yield part["text"]
                            except Exception:
                                continue
