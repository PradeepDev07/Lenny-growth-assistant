import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.llm.base import LLMResponse
from backend.app.llm.router import ModelRouter, select_best_ollama_model


@pytest.fixture
def router():
    return ModelRouter()


@pytest.fixture
def client():
    return TestClient(app)


def test_router_default_chains(router):
    qa_chain = router.get_chain_for_task("retrieval_qa")
    assert qa_chain[0] == ("gemini", "gemini-2.5-flash")

    essay_chain = router.get_chain_for_task("essay_generation")
    assert essay_chain[0] == ("openrouter", "openrouter/free")

    offline_chain = router.get_chain_for_task("offline_demo_mode")
    assert offline_chain[0] == ("ollama", "llama3.2:3b")


def test_router_override(router):
    router.set_task_override("retrieval_qa", "ollama", "llama3.2:3b")
    chain = router.get_chain_for_task("retrieval_qa")
    assert chain[0] == ("ollama", "llama3.2:3b")
    routes = router.get_current_routes()
    assert routes["retrieval_qa"]["provider"] == "ollama"
    assert routes["retrieval_qa"]["is_overridden"] is True


@pytest.mark.asyncio
async def test_router_fallback_execution():
    custom_router = ModelRouter()
    # Configure retrieval_qa chain to: primary (fails), secondary (succeeds)
    mock_success_response = LLMResponse(
        text="Fallback answer succeeded",
        provider="openrouter",
        model="anthropic/claude-3.5-sonnet",
        latency_ms=120.0,
    )

    with patch.object(custom_router, "get_provider_instance") as mock_get_provider:
        # Mock primary (gemini) failing
        mock_gemini = AsyncMock()
        mock_gemini.is_available.return_value = True
        mock_gemini.generate.side_effect = RuntimeError("Gemini 429 Quota Exceeded")

        # Mock secondary (openrouter) succeeding
        mock_openrouter = AsyncMock()
        mock_openrouter.is_available.return_value = True
        mock_openrouter.generate.return_value = mock_success_response

        def side_effect(provider_name, model_id):
            if provider_name == "gemini":
                return mock_gemini
            elif provider_name == "openrouter":
                return mock_openrouter
            return AsyncMock()

        mock_get_provider.side_effect = side_effect

        resp, meta = await custom_router.generate_for_task(
            task="retrieval_qa",
            messages=[{"role": "user", "content": "test question"}],
        )

        assert resp.text == "Fallback answer succeeded"
        assert meta["fallback_used"] is True
        assert meta["fallback_from"] == "gemini"
        assert meta["provider"] == "openrouter"
        assert len(custom_router.routing_audit_logs) == 1


def test_config_api_endpoints(client):
    # GET /config
    resp = client.get("/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "routes" in data
    assert "retrieval_qa" in data["routes"]
    assert "providers" in data
    assert "recent_routing_logs" in data

    # POST /config - valid override
    override_resp = client.post(
        "/config",
        json={"task": "retrieval_qa", "provider": "ollama", "model": "llama3.2:3b"},
    )
    assert override_resp.status_code == 200
    override_data = override_resp.json()
    assert override_data["status"] == "updated"
    assert override_data["effective_routes"]["retrieval_qa"]["provider"] == "ollama"

    # POST /config - invalid task
    bad_task_resp = client.post(
        "/config",
        json={"task": "invalid_task", "provider": "ollama", "model": "llama3.2:3b"},
    )
    assert bad_task_resp.status_code == 400


def test_select_best_ollama_model():
    # Empty
    assert select_best_ollama_model([]) is None

    # Exact match
    models = ["llama2-uncensored:latest", "qwen3.5:cloud", "llama3.2:3b"]
    assert select_best_ollama_model(models, "llama3.2:3b") == "llama3.2:3b"

    # Requested missing: prefer offline/local over -cloud
    models_no_default = ["qwen3.5:cloud", "llama2-uncensored:latest", "deepseek-v3.1:cloud"]
    assert select_best_ollama_model(models_no_default, "llama3.2:3b") == "llama2-uncensored:latest"

    # All cloud models: fallback to first
    cloud_only = ["qwen3.5:cloud", "deepseek-v3.1:cloud"]
    assert select_best_ollama_model(cloud_only, "llama3.2:3b") == "qwen3.5:cloud"


@pytest.mark.asyncio
async def test_resolve_ollama_model_dynamic_substitution():
    custom_router = ModelRouter()

    with patch("backend.app.llm.router.OllamaProvider") as mock_provider_cls:
        mock_instance = AsyncMock()
        mock_instance.is_available.return_value = True
        mock_instance.get_installed_models.return_value = ["llama2-uncensored:latest", "qwen3.5:cloud"]
        mock_provider_cls.return_value = mock_instance

        # Test exact match
        resolved, was_sub = await custom_router.resolve_ollama_model("llama2-uncensored:latest")
        assert resolved == "llama2-uncensored:latest"
        assert was_sub is False

        # Test fallback substitution
        resolved, was_sub = await custom_router.resolve_ollama_model("llama3.2:3b")
        assert resolved == "llama2-uncensored:latest"
        assert was_sub is True


@pytest.mark.asyncio
async def test_resolve_ollama_model_unavailable():
    custom_router = ModelRouter()

    with patch("backend.app.llm.router.OllamaProvider") as mock_provider_cls:
        mock_instance = AsyncMock()
        mock_instance.is_available.return_value = False
        mock_provider_cls.return_value = mock_instance

        resolved, was_sub = await custom_router.resolve_ollama_model("llama3.2:3b")
        assert resolved is None
        assert was_sub is False


@pytest.mark.asyncio
async def test_ollama_dynamic_fallback_in_generate():
    custom_router = ModelRouter()

    mock_ollama_response = LLMResponse(
        text="Offline answer from substituted model",
        provider="ollama",
        model="llama2-uncensored:latest",
        latency_ms=85.0,
    )

    with patch.object(custom_router, "resolve_ollama_model") as mock_resolve:
        mock_resolve.return_value = ("llama2-uncensored:latest", True)

        with patch.object(custom_router, "get_provider_instance") as mock_get_provider:
            mock_ollama = AsyncMock()
            mock_ollama.is_available.return_value = True
            mock_ollama.generate.return_value = mock_ollama_response
            mock_get_provider.return_value = mock_ollama

            resp, meta = await custom_router.generate_for_task(
                task="offline_demo_mode",
                messages=[{"role": "user", "content": "hi"}],
            )

            assert resp.text == "Offline answer from substituted model"
            assert meta["provider"] == "ollama"
            assert meta["model"] == "llama2-uncensored:latest"
            assert meta["fallback_used"] is True
            assert meta["fallback_from"] == "llama3.2:3b"

