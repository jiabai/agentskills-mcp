import pytest

from mcp_agentskills.config.settings import settings
from mcp_agentskills.core.security.password import verify_password
from mcp_agentskills.repositories.skill import SkillRepository
from mcp_agentskills.repositories.user import UserRepository
from mcp_agentskills.services.skill import SkillService
from mcp_agentskills.services.user import UserService


@pytest.mark.asyncio
async def test_update_and_change_password(async_session):
    user_repo = UserRepository(async_session)
    user_service = UserService(user_repo)
    user = await user_repo.create(email="b@example.com", username="userb", password="pass1234")
    updated = await user_service.update_user(user, username="userb2")
    assert updated.username == "userb2"
    changed = await user_service.change_password(user, "newpass123")
    assert verify_password("newpass123", changed.hashed_password) is True


@pytest.mark.asyncio
async def test_delete_user_requires_password(async_session):
    user_repo = UserRepository(async_session)
    user_service = UserService(user_repo)
    user = await user_repo.create(email="c@example.com", username="userc", password="pass1234")
    deleted = await user_service.delete_user(user, "pass1234")
    assert deleted is True


@pytest.mark.asyncio
async def test_delete_user_removes_skill_dirs(async_session, tmp_path):
    original_path = settings.SKILL_STORAGE_PATH
    settings.SKILL_STORAGE_PATH = str(tmp_path)
    try:
        user_repo = UserRepository(async_session)
        skill_repo = SkillRepository(async_session)
        skill_service = SkillService(skill_repo)
        user = await user_repo.create(email="d@example.com", username="userd", password="pass1234")
        await skill_service.create_skill(user, name="skillx", description="desc")
        skill_path = tmp_path / str(user.id) / "skillx"
        assert skill_path.exists()
        user_service = UserService(user_repo)
        await user_service.delete_user(user, "pass1234")
        assert not skill_path.exists()
    finally:
        settings.SKILL_STORAGE_PATH = original_path
