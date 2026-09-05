from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional
from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    """Normalized response schema across all LLM providers."""
    text: str = Field(..., description="Generated text content")
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list, description="Tool calls if any")
    usage: Dict[str, Any] = Field(default_factory=dict, description="Token usage statistics")
    latency_ms: float = Field(0.0, description="Round-trip latency in milliseconds")
    provider: str = Field(..., description="Provider name: gemini, openrouter, or ollama")
    model: str = Field(..., description="Exact model ID used")


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    def __init__(self, model: str):
        self.model = model

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """Generate a complete completion."""
        pass

    @abstractmethod
    async def stream(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """Stream completion tokens."""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if provider credentials/endpoint are reachable and valid."""
        pass
