import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.llm.base import LLMResponse
from backend.app.llm.router import ModelRouter


@pytest.fixture
def router():
    return ModelRouter()


@pytest.fixture
def client():
    return TestClient(app)


def test_router_default_chains(router):
    qa_chain = router.get_chain_for_task("retrieval_qa")
    assert qa_chain[0][0] == "gemini"

    essay_chain = router.get_chain_for_task("essay_generation")
    assert essay_chain[0][0] == "openrouter"

    offline_chain = router.get_chain_for_task("offline_demo_mode")
    assert offline_chain[0][0] == "ollama"


def test_router_override(router):
    router.set_task_override("retrieval_qa", "ollama", "llama3.1:8b")
    chain = router.get_chain_for_task("retrieval_qa")
    assert chain[0] == ("ollama", "llama3.1:8b")
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
        json={"task": "retrieval_qa", "provider": "ollama", "model": "llama3.1:8b"},
    )
    assert override_resp.status_code == 200
    override_data = override_resp.json()
    assert override_data["status"] == "updated"
    assert override_data["effective_routes"]["retrieval_qa"]["provider"] == "ollama"

    # POST /config - invalid task
    bad_task_resp = client.post(
        "/config",
        json={"task": "invalid_task", "provider": "ollama", "model": "llama3.1:8b"},
    )
    assert bad_task_resp.status_code == 400
