from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path

from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from mcp_agentskills.config.settings import settings
from mcp_agentskills.core.security.jwt_utils import decode_token
from mcp_agentskills.db.session import get_async_session
from mcp_agentskills.repositories.request_metric import RequestMetricRepository


_REQUEST_WINDOW_SECONDS = 24 * 60 * 60
def _should_track_request(path: str) -> bool:
    if not path.startswith("/api/v1"):
        return False
    if path.startswith("/api/v1/auth"):
        return False
    if path.startswith("/api/v1/dashboard/metrics/"):
        return False
    return True


def _extract_user_id(request: Request) -> str | None:
    authorization = request.headers.get("authorization")
    if not authorization:
        return None
    if not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        return None
    try:
        payload = decode_token(token)
    except ValueError:
        return None
    if payload.get("type") != "access":
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    return str(user_id)


async def record_request(user_id: str, status_code: int) -> None:
    bucket_start = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    try:
        async for session in get_async_session():
            repo = RequestMetricRepository(session)
            await repo.upsert_hour_bucket(user_id, bucket_start, status_code < 400)
    except Exception:
        logger.warning("request_metrics_write_failed")


async def get_success_rate(user_id: str, window_seconds: int = _REQUEST_WINDOW_SECONDS) -> tuple[float | None, int]:
    window_end = datetime.now(timezone.utc)
    window_start = window_end - timedelta(seconds=window_seconds)
    async for session in get_async_session():
        repo = RequestMetricRepository(session)
        total, success = await repo.aggregate_window(user_id, window_start, window_end)
        if total == 0:
            return 0, 0
        rate = success / total * 100
        return rate, total
    return 0, 0


def configure_loguru() -> None:
    serialize = str(settings.LOG_FORMAT).lower() == "json"
    logger.remove()
    logger.add(sys.stderr, level=settings.LOG_LEVEL, serialize=serialize)
    log_file = str(settings.LOG_FILE).strip()
    if not log_file:
        return
    try:
        Path(log_file).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        logger.add(log_file, level=settings.LOG_LEVEL, serialize=serialize)
    except Exception:
        return


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
        except Exception:
            response = JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal Server Error",
                    "code": "INTERNAL_SERVER_ERROR",
                    "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                },
            )
        if _should_track_request(request.url.path):
            user_id = _extract_user_id(request)
            if user_id:
                await record_request(user_id, response.status_code)
        logger.info(f"{request.method} {request.url.path} {response.status_code}")
        return response
