from datetime import datetime, timezone

from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware


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
