import pytest

from mcp_agentskills.core.security.password import verify_password
from mcp_agentskills.repositories.user import UserRepository
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
