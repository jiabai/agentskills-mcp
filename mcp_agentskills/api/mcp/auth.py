import re
from collections.abc import AsyncGenerator, Callable
from datetime import timezone

try:
    from fastmcp.server.auth.auth import TokenVerifier
except Exception:
    class TokenVerifier:
        async def verify_token(self, token: str):
            raise NotImplementedError
from mcp.server.auth.provider import AccessToken
from sqlalchemy.ext.asyncio import AsyncSession

from mcp_agentskills.core.utils.user_context import set_current_user_id
from mcp_agentskills.db.session import get_async_session
from mcp_agentskills.repositories.token import TokenRepository
from mcp_agentskills.repositories.user import UserRepository
from mcp_agentskills.services.token import TokenService

SessionProvider = Callable[[], AsyncGenerator[AsyncSession, None]]

_token_pattern = re.compile(r"^ask_live_[0-9a-f]{64}$")


async def _default_session_provider() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_async_session():
        yield session


_session_provider: SessionProvider = _default_session_provider


def set_session_provider(provider: SessionProvider) -> None:
    global _session_provider
    _session_provider = provider


def reset_session_provider() -> None:
    global _session_provider
    _session_provider = _default_session_provider


class ApiTokenVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        if not _token_pattern.match(token):
            return None
        async for session in _session_provider():
            token_repo = TokenRepository(session)
            user_repo = UserRepository(session)
            service = TokenService(token_repo, user_repo)
            try:
                api_token = await service.validate_token(token)
            except ValueError:
                return None
            user = await user_repo.get_by_id(api_token.user_id)
            if not user or not user.is_active:
                return None
            set_current_user_id(str(user.id))
            expires_at = None
            if api_token.expires_at:
                expires_at = int(api_token.expires_at.replace(tzinfo=timezone.utc).timestamp())
            return AccessToken(token=token, client_id=str(user.id), scopes=[], expires_at=expires_at)
