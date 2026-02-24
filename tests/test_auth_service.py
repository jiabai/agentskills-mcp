import pytest

from mcp_agentskills.core.security.jwt_utils import decode_token
from mcp_agentskills.models.user import User
from mcp_agentskills.repositories.base import BaseRepository
from mcp_agentskills.repositories.user import UserRepository
from mcp_agentskills.schemas.user import UserInDB
from mcp_agentskills.services.auth import AuthService


@pytest.mark.asyncio
async def test_register_login_refresh(async_session):
    user_repo = UserRepository(async_session)
    auth_service = AuthService(user_repo)
    user = await auth_service.register(email="a@example.com", username="usera", password="pass1234")
    token_pair = await auth_service.login(email="a@example.com", password="pass1234")
    access_payload = decode_token(token_pair.access_token)
    refresh_payload = decode_token(token_pair.refresh_token)
    assert access_payload["sub"] == str(user.id)
    assert refresh_payload["sub"] == str(user.id)
    refreshed = await auth_service.refresh_token(token_pair.refresh_token)
    refreshed_payload = decode_token(refreshed.access_token)
    assert refreshed_payload["sub"] == str(user.id)


@pytest.mark.asyncio
async def test_base_repository_crud(async_session):
    repo = BaseRepository(async_session)
    created = await repo.create(
        User,
        email="base@example.com",
        username="baseuser",
        hashed_password="hashed",
    )
    fetched = await repo.get(User, created.id)
    assert fetched is not None
    updated = await repo.update(fetched, username="updateduser")
    assert updated.username == "updateduser"
    await repo.delete(updated)
    missing = await repo.get(User, created.id)
    assert missing is None


def test_user_in_db_has_hashed_password():
    assert UserInDB.model_fields.get("hashed_password") is not None
