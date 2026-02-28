from contextlib import AsyncExitStack, asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
import psutil

from mcp_agentskills.api.mcp import (
    McpAppProxy,
    ensure_mcp_initialized,
    get_http_app,
    get_sse_app,
    shutdown_mcp,
)
from mcp_agentskills.api.router import api_router
from mcp_agentskills.config.settings import settings
from mcp_agentskills.core.middleware.logging import RequestLoggingMiddleware
from mcp_agentskills.core.middleware.rate_limit import RateLimitMiddleware
from mcp_agentskills.db.session import engine, init_db


class _SlashPathMiddleware:
    def __init__(self, app: FastAPI, paths: set[str]):
        self.app = app
        self.paths = paths

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            path = scope.get("path")
            if path in self.paths:
                updated = dict(scope)
                updated["path"] = f"{path}/"
                updated["raw_path"] = f"{path}/".encode()
                scope = updated
        await self.app(scope, receive, send)


@asynccontextmanager
async def lifespan(_application: FastAPI):
    await init_db()
    await ensure_mcp_initialized()
    async with AsyncExitStack() as stack:
        for mcp_app in (get_http_app(), get_sse_app()):
            router = getattr(mcp_app, "router", None)
            lifespan_context = getattr(router, "lifespan_context", None) if router else None
            if lifespan_context:
                await stack.enter_async_context(lifespan_context(mcp_app))
        yield
    await shutdown_mcp()


def create_application() -> FastAPI:
    application = FastAPI(lifespan=lifespan, redirect_slashes=False)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(RequestLoggingMiddleware)
    application.add_middleware(RateLimitMiddleware)
    application.add_middleware(_SlashPathMiddleware, paths={"/mcp", "/sse"})
    application.include_router(api_router, prefix="/api/v1")
    application.mount("/mcp", McpAppProxy(get_http_app))
    application.mount("/sse", McpAppProxy(get_sse_app))

    async def _check_db_connection() -> bool:
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    @application.get("/health")
    async def health():
        db_connected = await _check_db_connection()
        status_code = 200 if db_connected else 503
        payload = {
            "status": "healthy" if db_connected else "unhealthy",
            "db_connected": db_connected,
        }
        return JSONResponse(status_code=status_code, content=payload)

    @application.get("/metrics")
    async def metrics():
        db_connected = await _check_db_connection()
        skill_path = Path(settings.SKILL_STORAGE_PATH)
        disk = psutil.disk_usage(str(skill_path))
        memory = psutil.virtual_memory()
        return {
            "db_connected": db_connected,
            "disk_usage_percent": disk.percent,
            "memory_usage_percent": memory.percent,
            "cpu_usage_percent": psutil.cpu_percent(),
        }

    def _error_payload(detail: object, code: str) -> dict:
        return {
            "detail": detail,
            "code": code,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _code_for_status(status_code: int) -> str:
        return {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            409: "CONFLICT",
            422: "VALIDATION_ERROR",
        }.get(status_code, "HTTP_ERROR")

    @application.exception_handler(HTTPException)
    async def http_exception_handler(_request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(exc.detail, _code_for_status(exc.status_code)),
        )

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(_request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=_error_payload(exc.errors(), "VALIDATION_ERROR"),
        )

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(_request: Request, _exc: Exception):
        return JSONResponse(
            status_code=500,
            content=_error_payload("Internal Server Error", "INTERNAL_SERVER_ERROR"),
        )

    return application


app = create_application()
