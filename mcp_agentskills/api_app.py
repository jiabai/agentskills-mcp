from contextlib import AsyncExitStack, asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from mcp_agentskills.api.mcp import (
    McpAppProxy,
    ensure_mcp_initialized,
    get_http_app,
    get_sse_app,
    shutdown_mcp,
)
from mcp_agentskills.api.router import api_router
from mcp_agentskills.config.settings import settings
from mcp_agentskills.core.middleware.rate_limit import RateLimitMiddleware
from mcp_agentskills.db.session import init_db


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
    application.add_middleware(RateLimitMiddleware)
    application.add_middleware(_SlashPathMiddleware, paths={"/mcp", "/sse"})
    application.include_router(api_router, prefix="/api/v1")
    application.mount("/mcp", McpAppProxy(get_http_app))
    application.mount("/sse", McpAppProxy(get_sse_app))

    @application.get("/health")
    async def health():
        return {"status": "healthy"}

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

    return application


app = create_application()
