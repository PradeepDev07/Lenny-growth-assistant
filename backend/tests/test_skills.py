import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.session import init_db, SessionLocal
from backend.app.models.session import SessionModel
from backend.app.llm.base import LLMResponse
from backend.app.skills.ship30 import ship30_skill


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.asyncio
async def test_ship30_skill_generate():
    db = SessionLocal()
    session = SessionModel(title="Ship30 Skill Test Session")
    db.add(session)
    db.commit()
    db.refresh(session)

    mock_essay = (
        "# Why 90% of PMs Measure Activation Wrong\n\n"
        "Most product teams think account creation equals activation.\n"
        "They celebrate signups while 80% of users churn on day two.\n"
        "Elena Verna calls this the vanity onboarding trap.\n\n"
        "Real activation requires reaching the Aha moment in under 7 days."
    )
    mock_llm_response = LLMResponse(
        text=mock_essay,
        provider="openrouter",
        model="anthropic/claude-3.7-sonnet",
        latency_ms=250.0,
    )

    with patch("backend.app.llm.router.model_router.generate_for_task") as mock_gen:
        mock_gen.return_value = (
            mock_llm_response,
            {"task": "essay_generation", "provider": "openrouter", "model": "anthropic/claude-3.7-sonnet", "fallback_used": False},
        )

        res = await ship30_skill.generate_essay(
            session_id=session.id,
            topic="B2B PLG Activation Traps",
            db=db,
        )

        assert "Why 90% of PMs" in res["title"]
        assert "Elena Verna" in res["essay"]
        assert res["word_count"] > 20
        assert res["model_info"]["provider"] == "openrouter"

        # Verify persisted in session
        db.refresh(session)
        assert len(session.messages) == 1
        assert session.messages[0].content == mock_essay

    db.close()


def test_ship30_api_endpoint(client):
    # 1. Create session
    s_resp = client.post("/sessions", json={"title": "Ship 30 API Test"})
    assert s_resp.status_code == 201
    s_id = s_resp.json()["id"]

    mock_essay = (
        "# The 3 Growth Loops That Beat Traditional Funnels\n\n"
        "Funnels are linear and expensive.\n"
        "Loops are compounding systems that generate their own fuel.\n"
        "Brian Balfour pioneered this shift at HubSpot."
    )
    mock_llm_response = LLMResponse(
        text=mock_essay,
        provider="openrouter",
        model="anthropic/claude-3.7-sonnet",
        latency_ms=210.0,
    )

    with patch("backend.app.llm.router.model_router.generate_for_task") as mock_gen:
        mock_gen.return_value = (
            mock_llm_response,
            {"task": "essay_generation", "provider": "openrouter", "model": "anthropic/claude-3.7-sonnet", "fallback_used": False},
        )

        # 2. Call Ship30 endpoint
        res = client.post(
            f"/sessions/{s_id}/skills/ship30",
            json={"topic": "Growth Loops vs Funnels"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert "Growth Loops" in data["data"]["title"]
        assert data["data"]["model_info"]["provider"] == "openrouter"
