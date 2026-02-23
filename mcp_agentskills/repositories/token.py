from datetime import datetime, timezone

from sqlalchemy import select

from mcp_agentskills.models.token import APIToken
from mcp_agentskills.repositories.base import BaseRepository


class TokenRepository(BaseRepository):
    async def get_by_id(self, token_id: str) -> APIToken | None:
        result = await self.session.execute(select(APIToken).where(APIToken.id == token_id))
        return result.scalar_one_or_none()

    async def get_by_hash(self, token_hash: str) -> APIToken | None:
        result = await self.session.execute(select(APIToken).where(APIToken.token_hash == token_hash))
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: str) -> list[APIToken]:
        result = await self.session.execute(select(APIToken).where(APIToken.user_id == user_id))
        return list(result.scalars().all())

    async def create(
        self,
        user_id: str,
        name: str,
        token_hash: str,
        expires_at: datetime | None,
    ) -> APIToken:
        token = APIToken(
            user_id=user_id,
            name=name,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(token)
        await self.session.commit()
        await self.session.refresh(token)
        return token

    async def mark_used(self, token: APIToken) -> APIToken:
        token.last_used_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(token)
        return token

    async def revoke(self, token: APIToken) -> APIToken:
        token.is_active = False
        await self.session.commit()
        await self.session.refresh(token)
        return token
