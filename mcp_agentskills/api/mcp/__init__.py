import asyncio
import re
from collections.abc import AsyncGenerator, Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.types import Receive, Scope, Send
from sqlalchemy.ext.asyncio import AsyncSession

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
from mcp_agentskills.config.settings import settings
from mcp_agentskills.core.utils.user_context import set_current_user_id
from mcp_agentskills.db.session import get_async_session
from mcp_agentskills.repositories.token import TokenRepository
from mcp_agentskills.repositories.user import UserRepository
from mcp_agentskills.services.token import TokenService

_mcp_app: Any | None = None
_mcp_service: Any | None = None
_initialized = False
_init_lock = asyncio.Lock()
_init_error: Exception | None = None
_token_pattern = re.compile(r"^ask_live_[0-9a-f]{64}$")
SessionProvider = Callable[[], AsyncGenerator[AsyncSession, None]]
_session_provider: SessionProvider = get_async_session


def _error_payload(detail: object, code: str) -> dict:
    return {
        "detail": detail,
        "code": code,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def set_mcp_session_provider(provider: SessionProvider) -> None:
    global _session_provider
    _session_provider = provider


def reset_mcp_session_provider() -> None:
    global _session_provider
    _session_provider = get_async_session


def _extract_bearer_token(scope: Scope) -> str | None:
    headers = scope.get("headers") or []
    for key, value in headers:
        if key.decode().lower() == "authorization":
            auth_value = value.decode()
            parts = auth_value.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                return parts[1]
            return None
    return None


def _map_token_error(message: str) -> str:
    lowered = message.lower()
    if "expired" in lowered:
        return "TOKEN_EXPIRED"
    if "revoked" in lowered:
        return "TOKEN_REVOKED"
    if "not found" in lowered:
        return "TOKEN_NOT_FOUND"
    return "TOKEN_NOT_FOUND"


async def _send_error(
    scope: Scope,
    receive: Receive,
    send: Send,
    detail: str,
    code: str,
    status_code: int = 401,
) -> None:
    response = JSONResponse(status_code=status_code, content=_error_payload(detail, code))
    await response(scope, receive, send)


async def _authorize_mcp_request(scope: Scope, receive: Receive, send: Send) -> bool:
    token = _extract_bearer_token(scope)
    if not token or not _token_pattern.match(token):
        await _send_error(scope, receive, send, "Invalid token format", "INVALID_TOKEN_FORMAT")
        return False
    async for session in _session_provider():
        token_repo = TokenRepository(session)
        user_repo = UserRepository(session)
        service = TokenService(token_repo, user_repo)
        try:
            api_token = await service.validate_token(token)
        except ValueError as exc:
            code = _map_token_error(str(exc))
            await _send_error(scope, receive, send, str(exc), code)
            return False
        user = await user_repo.get_by_id(api_token.user_id)
        if not user or not user.is_active:
            await _send_error(scope, receive, send, "Token revoked", "TOKEN_REVOKED")
            return False
        set_current_user_id(str(user.id))
        return True
    await _send_error(scope, receive, send, "Token not found", "TOKEN_NOT_FOUND")
    return False


def _build_fallback_app() -> Starlette:
    async def handler(_request):
        return JSONResponse(status_code=401, content=_error_payload("Unauthorized", "UNAUTHORIZED"))

    return Starlette(
        routes=[
            Route(
                "/{path:path}",
                handler,
                methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            ),
        ],
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
        _mcp_app.service_config.metadata["skill_dir"] = str(Path(settings.SKILL_STORAGE_PATH).resolve())
        service = MCPService(service_config=_mcp_app.service_config)
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
        if scope.get("type") == "http":
            authorized = await _authorize_mcp_request(scope, receive, send)
            if not authorized:
                set_current_user_id(None)
                return
        await ensure_mcp_initialized()
        app = self._app_getter()
        await app(scope, receive, send)
        set_current_user_id(None)


__all__ = [
    "McpAppProxy",
    "ensure_mcp_initialized",
    "get_http_app",
    "get_sse_app",
    "reset_mcp_session_provider",
    "set_mcp_session_provider",
    "shutdown_mcp",
]
