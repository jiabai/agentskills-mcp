from collections import deque
import asyncio
from datetime import datetime, timezone
import sys
import time
from pathlib import Path

from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from mcp_agentskills.config.settings import settings
from mcp_agentskills.core.security.jwt_utils import decode_token


_REQUEST_WINDOW_SECONDS = 24 * 60 * 60
_request_history: dict[str, deque[tuple[float, bool]]] = {}
_request_lock = asyncio.Lock()


def _should_track_request(path: str) -> bool:
    if not path.startswith("/api/v1"):
        return False
    if path.startswith("/api/v1/auth"):
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
    now = time.time()
    cutoff = now - _REQUEST_WINDOW_SECONDS
    async with _request_lock:
        history = _request_history.setdefault(user_id, deque())
        history.append((now, status_code < 400))
        while history and history[0][0] < cutoff:
            history.popleft()


async def get_success_rate(user_id: str, window_seconds: int = _REQUEST_WINDOW_SECONDS) -> tuple[float | None, int]:
    now = time.time()
    cutoff = now - window_seconds
    async with _request_lock:
        history = _request_history.get(user_id)
        if not history:
            return None, 0
        while history and history[0][0] < cutoff:
            history.popleft()
        total = len(history)
        if total == 0:
            return None, 0
        success = sum(1 for _, ok in history if ok)
        rate = success / total * 100
        return rate, total


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
