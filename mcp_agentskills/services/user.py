from mcp_agentskills.core.security.password import get_password_hash, verify_password
from mcp_agentskills.core.utils.skill_storage import delete_skill_dir
from mcp_agentskills.models.user import User
from mcp_agentskills.repositories.skill import SkillRepository
from mcp_agentskills.repositories.user import UserRepository


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def update_user(self, user: User, **fields) -> User:
        return await self.user_repo.update(user, **fields)

    async def change_password(self, user: User, new_password: str) -> User:
        hashed = get_password_hash(new_password)
        return await self.user_repo.update(user, hashed_password=hashed)

    async def delete_user(self, user: User, password: str) -> bool:
        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid password")
        skill_repo = SkillRepository(self.user_repo.session)
        skills = await skill_repo.list_by_user(user.id)
        for skill in skills:
            delete_skill_dir(user.id, skill.name)
        await self.user_repo.delete(user)
        return True
