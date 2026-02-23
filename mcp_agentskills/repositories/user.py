from sqlalchemy import select

from mcp_agentskills.core.security.password import get_password_hash
from mcp_agentskills.models.user import User
from mcp_agentskills.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    async def get_by_id(self, user_id: str) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def create(self, email: str, username: str, password: str) -> User:
        user = User(email=email, username=username, hashed_password=get_password_hash(password))
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update(self, user: User, **fields) -> User:
        for key, value in fields.items():
            setattr(user, key, value)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
        await self.session.commit()
