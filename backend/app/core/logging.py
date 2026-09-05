import json
import logging
import sys
import time
from datetime import datetime, timezone
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter for production observability."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include custom attributes from record
        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            log_obj.update(record.extra_fields)

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


def setup_structured_logging():
    """Configure root logger to use JSON formatting."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Logs HTTP request/response metrics with duration in milliseconds."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        logger = logging.getLogger("http_access")

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            log_record = logging.LogRecord(
                name="http_access",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg=f"{request.method} {request.url.path} completed with {response.status_code}",
                args=(),
                exc_info=None,
            )
            log_record.extra_fields = {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            }
            logger.handle(log_record)
            return response
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                f"Unhandled exception during {request.method} {request.url.path}: {exc}",
                exc_info=True,
                extra={"method": request.method, "path": request.url.path, "duration_ms": duration_ms},
            )
            raise
