import pytest

from mcp_agentskills.repositories.skill import SkillRepository
from mcp_agentskills.repositories.user import UserRepository
from mcp_agentskills.services.skill import SkillService


@pytest.mark.asyncio
async def test_create_update_delete_skill(async_session, tmp_path, monkeypatch):
    monkeypatch.setenv("SKILL_STORAGE_PATH", str(tmp_path))
    user_repo = UserRepository(async_session)
    skill_repo = SkillRepository(async_session)
    skill_service = SkillService(skill_repo)
    user = await user_repo.create(email="e@example.com", username="usere", password="pass1234")
    created = await skill_service.create_skill(user, name="skillx", description="desc")
    skills = await skill_service.list_skills(user)
    assert len(skills) == 1
    updated = await skill_service.update_skill(user, created.id, description="new")
    assert updated.description == "new"
    deleted = await skill_service.delete_skill(user, created.id)
    assert deleted is True


def test_skill_unique_constraint_name():
    from mcp_agentskills.models.skill import Skill

    constraint_names = {constraint.name for constraint in Skill.__table__.constraints if constraint.name}
    assert "uix_user_skill_name" in constraint_names


@pytest.mark.asyncio
async def test_rename_skill_updates_directory(async_session, tmp_path):
    from mcp_agentskills.config.settings import settings

    original_path = settings.SKILL_STORAGE_PATH
    settings.SKILL_STORAGE_PATH = str(tmp_path)
    try:
        user_repo = UserRepository(async_session)
        skill_repo = SkillRepository(async_session)
        skill_service = SkillService(skill_repo)
        user = await user_repo.create(email="f@example.com", username="userf", password="pass1234")
        created = await skill_service.create_skill(user, name="skillold", description="desc")
        old_path = tmp_path / str(user.id) / "skillold"
        assert old_path.exists()
        updated = await skill_service.update_skill(user, created.id, name="skillnew")
        new_path = tmp_path / str(user.id) / "skillnew"
        assert updated.name == "skillnew"
        assert new_path.exists()
        assert not old_path.exists()
    finally:
        settings.SKILL_STORAGE_PATH = original_path
