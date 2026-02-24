from pathlib import Path

from mcp_agentskills.config.settings import settings
from mcp_agentskills.core.utils.skill_storage import (
    MAX_FILES_PER_SKILL,
    MAX_FILE_SIZE,
    MAX_TOTAL_SIZE,
    create_skill_dir,
    delete_skill_dir,
    get_safe_skill_path,
    get_user_skill_dir,
    list_files,
    validate_filename,
)
from mcp_agentskills.models.skill import Skill
from mcp_agentskills.models.user import User
from mcp_agentskills.repositories.skill import SkillRepository


class SkillService:
    def __init__(self, skill_repo: SkillRepository):
        self.skill_repo = skill_repo

    async def list_skills(
        self, user: User, skip: int = 0, limit: int = 100, query: str | None = None
    ) -> list[Skill]:
        return await self.skill_repo.list_by_user(user.id, skip=skip, limit=limit, query=query)

    async def get_skill(self, user: User, skill_id: str) -> Skill:
        skill = await self.skill_repo.get_by_id(skill_id)
        if not skill or skill.user_id != user.id:
            raise ValueError("Skill not found")
        return skill

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
        skill = await self.get_skill(user, skill_id)
        return await self.skill_repo.update(skill, **fields)

    async def delete_skill(self, user: User, skill_id: str) -> bool:
        skill = await self.get_skill(user, skill_id)
        await self.skill_repo.delete(skill)
        delete_skill_dir(user.id, skill.name)
        return True

    async def list_skill_files(self, user: User, skill_id: str) -> list[str]:
        skill = await self.get_skill(user, skill_id)
        return list_files(user.id, skill.name)

    async def upload_file(self, user: User, skill_id: str, filename: str, content: bytes) -> str:
        skill = await self.get_skill(user, skill_id)
        valid, error = validate_filename(filename)
        if not valid:
            raise ValueError(error)
        if len(content) > MAX_FILE_SIZE:
            raise ValueError("File too large")
        existing = list_files(user.id, skill.name)
        if len(existing) >= MAX_FILES_PER_SKILL:
            raise ValueError("Too many files in skill")
        skill_dir = get_user_skill_dir(user.id, skill.name)
        total_size = 0
        for rel_path in existing:
            file_path = skill_dir / rel_path
            if file_path.exists() and file_path.is_file():
                total_size += file_path.stat().st_size
        if total_size + len(content) > MAX_TOTAL_SIZE:
            raise ValueError("Total skill size limit exceeded")
        base_dir = Path(settings.SKILL_STORAGE_PATH)
        safe_path = get_safe_skill_path(base_dir, user.id, skill.name, filename)
        if not safe_path:
            raise ValueError("Invalid file path")
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_bytes(content)
        return filename
