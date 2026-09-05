import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.session import init_db, SessionLocal
from backend.app.models.session import SessionModel
from backend.app.llm.base import LLMResponse
from backend.app.services.artifact_service import sanitize_html_artifact, artifact_service


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()


@pytest.fixture
def client():
    return TestClient(app)


def test_sanitize_html_security():
    malicious_html = """
    <!DOCTYPE html>
    <html>
      <head>
        <script src="https://evil-attacker.com/malicious.js"></script>
        <style>body { color: blue; }</style>
      </head>
      <body>
        <h1>Calculator</h1>
        <script>
          const stolen = document.cookie;
          localStorage.setItem("key", "val");
          window.parent.postMessage("hacked", "*");
        </script>
      </body>
    </html>
    """
    cleaned = sanitize_html_artifact(malicious_html)

    # Assert external script src is removed
    assert "https://evil-attacker.com/malicious.js" not in cleaned
    assert "external script removed for security" in cleaned

    # Assert dangerous APIs neutralized
    assert "document.cookie" not in cleaned
    assert "localStorage" not in cleaned
    assert "window.parent" not in cleaned

    # Assert legitimate elements preserved
    assert "<h1>Calculator</h1>" in cleaned
    assert "<style>body { color: blue; }</style>" in cleaned


@pytest.mark.asyncio
async def test_artifact_service_generate():
    db = SessionLocal()
    session = SessionModel(title="Artifact Service Test Session")
    db.add(session)
    db.commit()
    db.refresh(session)

    mock_html = "<div id='app'><h2>Growth Calculator</h2></div>"
    mock_llm_response = LLMResponse(
        text=f"```html\n{mock_html}\n```",
        provider="gemini",
        model="gemini-2.0-flash",
        latency_ms=190.0,
    )

    with patch("backend.app.llm.router.model_router.generate_for_task") as mock_gen:
        mock_gen.return_value = (
            mock_llm_response,
            {"task": "artifact_generation", "provider": "gemini", "model": "gemini-2.0-flash", "fallback_used": False},
        )

        art = await artifact_service.generate_artifact(
            session_id=session.id,
            title="SaaS CAC Calculator",
            artifact_type="html",
            prompt="Build a slider for CAC and LTV",
            db=db,
        )

        assert art.title == "SaaS CAC Calculator"
        assert art.type == "html"
        assert "<div id='app'>" in art.content
        assert art.session_id == session.id

    db.close()


def test_artifacts_api_endpoints(client):
    # 1. Create session
    s_resp = client.post("/sessions", json={"title": "Artifact API Session"})
    assert s_resp.status_code == 201
    s_id = s_resp.json()["id"]

    mock_html = "<div class='chart'>Growth Loop Chart</div>"
    mock_llm_response = LLMResponse(
        text=mock_html,
        provider="gemini",
        model="gemini-2.0-flash",
        latency_ms=175.0,
    )

    with patch("backend.app.llm.router.model_router.generate_for_task") as mock_gen:
        mock_gen.return_value = (
            mock_llm_response,
            {"task": "artifact_generation", "provider": "gemini", "model": "gemini-2.0-flash", "fallback_used": False},
        )

        # 2. Create artifact
        art_resp = client.post(
            f"/sessions/{s_id}/artifacts",
            json={
                "title": "Growth Loop Diagram",
                "type": "html",
                "prompt": "Create a diagram for viral and paid growth loops",
            },
        )
        assert art_resp.status_code == 201
        art_data = art_resp.json()
        art_id = art_data["id"]
        assert art_data["title"] == "Growth Loop Diagram"

        # 3. List artifacts in session
        list_resp = client.get(f"/sessions/{s_id}/artifacts")
        assert list_resp.status_code == 200
        items = list_resp.json()
        assert len(items) >= 1
        assert any(a["id"] == art_id for a in items)

        # 4. Get raw artifact
        raw_resp = client.get(f"/artifacts/{art_id}/raw")
        assert raw_resp.status_code == 200
        assert raw_resp.headers["content-type"].startswith("text/html")
        assert "Content-Security-Policy" in raw_resp.headers
        assert "<div class='chart'>" in raw_resp.text
