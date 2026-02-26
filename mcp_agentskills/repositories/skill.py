from typing import Any

from sqlalchemy import func, or_, select

from mcp_agentskills.models.skill import Skill
from mcp_agentskills.repositories.base import BaseRepository


class SkillRepository(BaseRepository):
    async def get_by_id(self, skill_id: str) -> Skill | None:
        result = await self.session.execute(select(Skill).where(Skill.id == skill_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, user_id: str, name: str) -> Skill | None:
        result = await self.session.execute(
            select(Skill).where(Skill.user_id == user_id, Skill.name == name),
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        query: str | None = None,
    ) -> list[Skill]:
        stmt = select(Skill).where(Skill.user_id == user_id)
        if query:
            pattern = f"%{query}%"
            stmt = stmt.where(or_(Skill.name.ilike(pattern), Skill.description.ilike(pattern)))
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_user(self, user_id: str, query: str | None = None) -> int:
        stmt = select(func.count()).select_from(Skill).where(Skill.user_id == user_id)
        if query:
            pattern = f"%{query}%"
            stmt = stmt.where(or_(Skill.name.ilike(pattern), Skill.description.ilike(pattern)))
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def create(self, model: Any = Skill, **data: Any) -> Skill:
        skill = Skill(**data)
        self.session.add(skill)
        await self.session.commit()
        await self.session.refresh(skill)
        return skill

    async def update(self, db_obj: Any, **data: Any) -> Skill:
        for key, value in data.items():
            setattr(db_obj, key, value)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, db_obj: Skill) -> None:
        await self.session.delete(db_obj)
        await self.session.commit()
