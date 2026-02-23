import asyncio
from collections.abc import Callable
from typing import Any

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.types import Receive, Scope, Send

from mcp_agentskills.api.mcp.auth import ApiTokenVerifier
from mcp_agentskills.api.mcp.http_handler import (
    create_http_app,
    get_http_app,
    set_http_app,
)
from mcp_agentskills.api.mcp.sse_handler import (
    create_sse_app,
    get_sse_app,
    set_sse_app,
)
_mcp_app: Any | None = None
_mcp_service: Any | None = None
_initialized = False
_init_lock = asyncio.Lock()
_init_error: Exception | None = None


def _build_fallback_app() -> Starlette:
    async def handler(request):
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)

    return Starlette(
        routes=[
            Route(
                "/{path:path}",
                handler,
                methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            )
        ]
    )


async def ensure_mcp_initialized() -> None:
    global _initialized
    global _mcp_app
    global _mcp_service
    global _init_error
    if _initialized:
        return
    async with _init_lock:
        if _initialized:
            return
        try:
            from flowllm.core.context import C
            from flowllm.core.flow import BaseToolFlow
            from flowllm.core.service.mcp_service import MCPService

            from mcp_agentskills.main import AgentSkillsMcpApp
        except Exception as exc:
            _init_error = exc
            fallback = _build_fallback_app()
            set_http_app(fallback)
            set_sse_app(fallback)
            _initialized = True
            return
        _mcp_app = AgentSkillsMcpApp("config=default")
        await _mcp_app.async_start()
        service = MCPService(service_config=_mcp_app.service_config)
        service.mcp.auth = ApiTokenVerifier()
        for flow in C.flow_dict.values():
            if isinstance(flow, BaseToolFlow):
                service.integrate_tool_flow(flow)
        _mcp_service = service
        set_http_app(create_http_app(service.mcp))
        set_sse_app(create_sse_app(service.mcp))
        _initialized = True


async def shutdown_mcp() -> None:
    global _initialized
    global _mcp_app
    global _mcp_service
    if not _initialized:
        return
    if _mcp_app:
        await _mcp_app.async_stop()
    _mcp_app = None
    _mcp_service = None
    set_http_app(None)
    set_sse_app(None)
    _initialized = False


class McpAppProxy:
    def __init__(self, app_getter: Callable[[], Any]):
        self._app_getter = app_getter

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        await ensure_mcp_initialized()
        app = self._app_getter()
        await app(scope, receive, send)


__all__ = [
    "McpAppProxy",
    "ensure_mcp_initialized",
    "get_http_app",
    "get_sse_app",
    "shutdown_mcp",
]
