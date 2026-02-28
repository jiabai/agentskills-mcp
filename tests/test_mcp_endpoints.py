import pytest
from datetime import datetime, timedelta, timezone

from mcp_agentskills.api.mcp import reset_mcp_session_provider, set_mcp_session_provider
from mcp_agentskills.repositories.token import TokenRepository
from mcp_agentskills.repositories.user import UserRepository
from mcp_agentskills.services.token import TokenService


@pytest.mark.asyncio
async def test_mcp_http_requires_auth(client):
    response = await client.post("/mcp")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_mcp_sse_requires_auth(client):
    response = await client.get("/sse")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_mcp_invalid_token_format_returns_code(client):
    response = await client.post("/mcp", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401
    payload = response.json()
    assert payload["code"] == "INVALID_TOKEN_FORMAT"


@pytest.mark.asyncio
async def test_mcp_token_not_found_returns_code(client, async_session):
    async def session_provider():
        yield async_session

    set_mcp_session_provider(session_provider)
    try:
        response = await client.post("/mcp", headers={"Authorization": "Bearer ask_live_" + "0" * 64})
        assert response.status_code == 401
        payload = response.json()
        assert payload["code"] == "TOKEN_NOT_FOUND"
    finally:
        reset_mcp_session_provider()


@pytest.mark.asyncio
async def test_mcp_token_revoked_returns_code(client, async_session):
    user_repo = UserRepository(async_session)
    user = await user_repo.create(email="revoked@example.com", username="revoked", password="pass1234")
    service = TokenService(TokenRepository(async_session), user_repo)
    token, value = await service.create_token_with_value(user, name="revoked")
    await service.token_repo.revoke(token)
    async def session_provider():
        yield async_session

    set_mcp_session_provider(session_provider)
    try:
        response = await client.post("/mcp", headers={"Authorization": f"Bearer {value}"})
        assert response.status_code == 401
        payload = response.json()
        assert payload["code"] == "TOKEN_REVOKED"
    finally:
        reset_mcp_session_provider()


@pytest.mark.asyncio
async def test_mcp_token_expired_returns_code(client, async_session):
    user_repo = UserRepository(async_session)
    user = await user_repo.create(email="expired@example.com", username="expired", password="pass1234")
    service = TokenService(TokenRepository(async_session), user_repo)
    expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    _, value = await service.create_token_with_value(user, name="expired", expires_at=expires_at)
    async def session_provider():
        yield async_session

    set_mcp_session_provider(session_provider)
    try:
        response = await client.post("/mcp", headers={"Authorization": f"Bearer {value}"})
        assert response.status_code == 401
        payload = response.json()
        assert payload["code"] == "TOKEN_EXPIRED"
    finally:
        reset_mcp_session_provider()
