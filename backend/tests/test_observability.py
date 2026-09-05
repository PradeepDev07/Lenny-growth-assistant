import json
import logging
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.logging import JSONFormatter


def test_json_log_formatter():
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="LLM call completed",
        args=(),
        exc_info=None,
    )
    record.extra_fields = {
        "provider": "gemini",
        "model": "gemini-2.0-flash",
        "latency_ms": 124.5,
        "tokens": 85,
    }

    formatted = formatter.format(record)
    data = json.loads(formatted)
    assert data["level"] == "INFO"
    assert data["message"] == "LLM call completed"
    assert data["provider"] == "gemini"
    assert data["model"] == "gemini-2.0-flash"
    assert data["latency_ms"] == 124.5


def test_observability_middleware_runs():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
