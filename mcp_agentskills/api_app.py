from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mcp_agentskills.api.mcp import (
    McpAppProxy,
    ensure_mcp_initialized,
    get_http_app,
    get_sse_app,
    shutdown_mcp,
)
from mcp_agentskills.api.router import api_router
from mcp_agentskills.config.settings import settings
from mcp_agentskills.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    app = FastAPI(lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix="/api/v1")
    app.add_route(
        "/mcp",
        McpAppProxy(get_http_app),
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )
    app.add_route(
        "/sse",
        McpAppProxy(get_sse_app),
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )
    app.mount("/mcp", McpAppProxy(get_http_app))
    app.mount("/sse", McpAppProxy(get_sse_app))

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    return app


app = create_application()
