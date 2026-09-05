import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.session import init_db


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()


@pytest.fixture
def client():
    return TestClient(app)


def test_session_crud_and_messages(client):
    # 1. Create a new session
    create_resp = client.post(
        "/sessions",
        json={"title": "Growth Strategy Test", "user_metadata": {"topic": "activation"}},
    )
    assert create_resp.status_code == 201
    session = create_resp.json()
    session_id = session["id"]
    assert session["title"] == "Growth Strategy Test"
    assert session["user_metadata"]["topic"] == "activation"
    assert session["message_count"] == 0

    # 2. List sessions
    list_resp = client.get("/sessions")
    assert list_resp.status_code == 200
    sessions = list_resp.json()
    assert any(s["id"] == session_id for s in sessions)

    # 3. Post user message
    msg_resp = client.post(
        f"/sessions/{session_id}/messages",
        json={"role": "user", "content": "How do I calculate time to value?"},
    )
    assert msg_resp.status_code == 201
    msg_data = msg_resp.json()
    assert msg_data["role"] == "user"
    assert msg_data["content"] == "How do I calculate time to value?"
    assert msg_data["session_id"] == session_id

    # 4. Fetch session detail
    detail_resp = client.get(f"/sessions/{session_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert len(detail["messages"]) == 1
    assert detail["messages"][0]["content"] == "How do I calculate time to value?"

    # 5. Fetch messages directly
    msgs_resp = client.get(f"/sessions/{session_id}/messages")
    assert msgs_resp.status_code == 200
    msgs = msgs_resp.json()
    assert len(msgs) == 1
    assert msgs[0]["id"] == msg_data["id"]

    # 6. Update session title
    patch_resp = client.patch(
        f"/sessions/{session_id}",
        json={"title": "Updated Growth Session"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["title"] == "Updated Growth Session"

    # 7. Delete session
    del_resp = client.delete(f"/sessions/{session_id}")
    assert del_resp.status_code == 204

    # 8. Assert 404 after deletion
    get_deleted = client.get(f"/sessions/{session_id}")
    assert get_deleted.status_code == 404
    err = get_deleted.json()
    assert "detail" in err or "error" in err
