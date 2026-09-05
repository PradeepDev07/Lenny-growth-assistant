import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.session import init_db, SessionLocal
from backend.app.models.session import SessionModel
from backend.app.llm.base import LLMResponse
from backend.app.agent.rag import rag_agent


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.asyncio
async def test_rag_agent_grounded_answer():
    db = SessionLocal()
    session = SessionModel(title="RAG Test Session")
    db.add(session)
    db.commit()
    db.refresh(session)

    mock_llm_response = LLMResponse(
        text="Elena Verna emphasizes that activation is the Aha moment [Elena Verna · B2B PLG].",
        provider="gemini",
        model="gemini-2.0-flash",
        latency_ms=150.0,
    )

    with patch("backend.app.llm.router.model_router.generate_for_task") as mock_gen:
        mock_gen.return_value = (
            mock_llm_response,
            {"task": "retrieval_qa", "provider": "gemini", "model": "gemini-2.0-flash", "fallback_used": False},
        )

        msg = await rag_agent.answer_query(
            session_id=session.id,
            user_query="How does Elena Verna define activation?",
            db=db,
        )

        assert msg.role == "assistant"
        assert "Elena Verna" in msg.content
        assert len(msg.sources) > 0
        assert any("Elena Verna" in s["source_title"] or "Elena Verna" in s["guest"] for s in msg.sources)
        assert msg.model_info["provider"] == "gemini"

    db.close()


@pytest.mark.asyncio
async def test_rag_agent_unretrieved_disclaimer():
    db = SessionLocal()
    session = SessionModel(title="Ungrounded Query Test")
    db.add(session)
    db.commit()
    db.refresh(session)

    # Empty query or query with 0 relevant hits in vector store
    msg = await rag_agent.answer_query(
        session_id=session.id,
        user_query="asldkfjqwpoeirusdfklj",
        db=db,
    )

    assert msg.role == "assistant"
    assert "could not find information" in msg.content.lower()
    assert len(msg.sources) == 0

    db.close()


def test_chat_api_endpoint(client):
    # 1. Create session
    s_resp = client.post("/sessions", json={"title": "Chat API Test"})
    assert s_resp.status_code == 201
    s_id = s_resp.json()["id"]

    mock_llm_response = LLMResponse(
        text="According to Brian Balfour, growth loops beat funnels [Brian Balfour · Growth Loops].",
        provider="gemini",
        model="gemini-2.0-flash",
        latency_ms=180.0,
    )

    with patch("backend.app.llm.router.model_router.generate_for_task") as mock_gen:
        mock_gen.return_value = (
            mock_llm_response,
            {"task": "retrieval_qa", "provider": "gemini", "model": "gemini-2.0-flash", "fallback_used": False},
        )

        # 2. Chat
        c_resp = client.post(
            f"/sessions/{s_id}/chat",
            json={"content": "Explain growth loops vs funnels according to Brian Balfour"},
        )
        assert c_resp.status_code == 200
        data = c_resp.json()
        assert data["role"] == "assistant"
        assert "Brian Balfour" in data["content"]
        assert len(data["sources"]) > 0
        assert data["model_info"]["provider"] == "gemini"
