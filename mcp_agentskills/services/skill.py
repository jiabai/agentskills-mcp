from mcp_agentskills.core.utils.skill_storage import create_skill_dir, delete_skill_dir
from mcp_agentskills.models.skill import Skill
from mcp_agentskills.models.user import User
from mcp_agentskills.repositories.skill import SkillRepository


class SkillService:
    def __init__(self, skill_repo: SkillRepository):
        self.skill_repo = skill_repo

    async def list_skills(self, user: User) -> list[Skill]:
        return await self.skill_repo.list_by_user(user.id)

    async def create_skill(self, user: User, name: str, description: str) -> Skill:
        if await self.skill_repo.get_by_name(user.id, name):
            raise ValueError("Skill already exists")
        path = create_skill_dir(user.id, name)
        return await self.skill_repo.create(
            user_id=user.id,
            name=name,
            description=description,
            skill_dir=str(path),
        )

    async def update_skill(self, user: User, skill_id: str, **fields) -> Skill:
        skill = await self.skill_repo.get_by_id(skill_id)
        if not skill or skill.user_id != user.id:
            raise ValueError("Skill not found")
        return await self.skill_repo.update(skill, **fields)

    async def delete_skill(self, user: User, skill_id: str) -> bool:
        skill = await self.skill_repo.get_by_id(skill_id)
        if not skill or skill.user_id != user.id:
            raise ValueError("Skill not found")
        await self.skill_repo.delete(skill)
        delete_skill_dir(user.id, skill.name)
        return True
