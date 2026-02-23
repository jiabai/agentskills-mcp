from sqlalchemy import select

from mcp_agentskills.models.skill import Skill
from mcp_agentskills.repositories.base import BaseRepository


class SkillRepository(BaseRepository):
    async def get_by_id(self, skill_id: str) -> Skill | None:
        result = await self.session.execute(select(Skill).where(Skill.id == skill_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, user_id: str, name: str) -> Skill | None:
        result = await self.session.execute(
            select(Skill).where(Skill.user_id == user_id, Skill.name == name)
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: str) -> list[Skill]:
        result = await self.session.execute(select(Skill).where(Skill.user_id == user_id))
        return list(result.scalars().all())

    async def create(self, user_id: str, name: str, description: str, skill_dir: str) -> Skill:
        skill = Skill(user_id=user_id, name=name, description=description, skill_dir=skill_dir)
        self.session.add(skill)
        await self.session.commit()
        await self.session.refresh(skill)
        return skill

    async def update(self, skill: Skill, **fields) -> Skill:
        for key, value in fields.items():
            setattr(skill, key, value)
        await self.session.commit()
        await self.session.refresh(skill)
        return skill

    async def delete(self, skill: Skill) -> None:
        await self.session.delete(skill)
        await self.session.commit()
