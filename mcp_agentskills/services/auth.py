from dataclasses import dataclass

from mcp_agentskills.core.security.jwt_utils import create_access_token, create_refresh_token, decode_token
from mcp_agentskills.core.security.password import verify_password
from mcp_agentskills.models.user import User
from mcp_agentskills.repositories.user import UserRepository


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register(self, email: str, username: str, password: str) -> User:
        if await self.user_repo.get_by_email(email):
            raise ValueError("Email already registered")
        if await self.user_repo.get_by_username(username):
            raise ValueError("Username already registered")
        return await self.user_repo.create(email=email, username=username, password=password)

    async def login(self, email: str, password: str) -> TokenPair:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")
        return TokenPair(
            access_token=create_access_token(subject=str(user.id)),
            refresh_token=create_refresh_token(subject=str(user.id)),
        )

    async def refresh_token(self, refresh_token: str) -> TokenPair:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")
        subject = payload.get("sub")
        if not subject:
            raise ValueError("Invalid token")
        user = await self.user_repo.get_by_id(subject)
        if not user:
            raise ValueError("User not found")
        return TokenPair(
            access_token=create_access_token(subject=str(user.id)),
            refresh_token=create_refresh_token(subject=str(user.id)),
        )
