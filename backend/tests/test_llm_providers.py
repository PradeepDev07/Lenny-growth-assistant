import pytest
from unittest.mock import patch, AsyncMock
from backend.app.llm.base import LLMResponse
from backend.app.llm.gemini_provider import GeminiProvider
from backend.app.llm.openrouter_provider import OpenRouterProvider
from backend.app.llm.ollama_provider import OllamaProvider


@pytest.mark.asyncio
async def test_gemini_provider_unconfigured():
    provider = GeminiProvider(api_key="")
    assert await provider.is_available() is False
    with pytest.raises(ValueError, match="GEMINI_API_KEY is not configured"):
        await provider.generate([{"role": "user", "content": "Hi"}])


@pytest.mark.asyncio
async def test_openrouter_provider_unconfigured():
    provider = OpenRouterProvider(api_key="")
    assert await provider.is_available() is False
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY is not configured"):
        await provider.generate([{"role": "user", "content": "Hi"}])


@pytest.mark.asyncio
async def test_ollama_provider_availability():
    provider = OllamaProvider(base_url="http://127.0.0.1:9999")
    # Non-existent port should return False without crashing
    assert await provider.is_available() is False


@pytest.mark.asyncio
async def test_gemini_provider_mocked_generate():
    provider = GeminiProvider(api_key="mock-key")
    mock_resp_data = {
        "candidates": [{
            "content": {
                "parts": [{"text": "Hello, I am Gemini!"}]
            }
        }],
        "usageMetadata": {"promptTokenCount": 5, "candidatesTokenCount": 7}
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.json = lambda: mock_resp_data
        mock_post.return_value = mock_resp

        res = await provider.generate([{"role": "user", "content": "Hello"}])
        assert isinstance(res, LLMResponse)
        assert res.text == "Hello, I am Gemini!"
        assert res.provider == "gemini"
        assert res.model == "gemini-2.5-flash"


@pytest.mark.asyncio
async def test_openrouter_provider_mocked_generate():
    provider = OpenRouterProvider(model="anthropic/claude-3.7-sonnet", api_key="mock-or-key")
    mock_resp_data = {
        "choices": [{
            "message": {"role": "assistant", "content": "Hello from OpenRouter Claude!"}
        }],
        "usage": {"total_tokens": 12}
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.json = lambda: mock_resp_data
        mock_post.return_value = mock_resp

        res = await provider.generate([{"role": "user", "content": "Hello"}])
        assert isinstance(res, LLMResponse)
        assert res.text == "Hello from OpenRouter Claude!"
        assert res.provider == "openrouter"
        assert res.model == "anthropic/claude-3.7-sonnet"

