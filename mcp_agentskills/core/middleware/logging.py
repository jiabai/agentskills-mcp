from datetime import datetime, timezone
import sys
from pathlib import Path

from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from mcp_agentskills.config.settings import settings


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
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
        logger.info(f"{request.method} {request.url.path} {response.status_code}")
        return response
