import httpx
import pytest

from mcp_agentskills.api_app import create_application
from mcp_agentskills.config.settings import settings


@pytest.mark.asyncio
async def test_register_login_refresh(client):
    register = await client.post(
        "/api/v1/auth/register",
        json={"email": "api@example.com", "username": "apiuser", "password": "pass1234"},
    )
    assert register.status_code == 201
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "api@example.com", "password": "pass1234"},
    )
    assert login.status_code == 200
    refresh_token = login.json()["refresh_token"]
    refreshed = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refreshed.status_code == 200


@pytest.mark.asyncio
async def test_refresh_requires_token(client):
    response = await client.post("/api/v1/auth/refresh", json={})
    assert response.status_code == 422
    payload = response.json()
    assert "detail" in payload
    assert "code" in payload
    assert "timestamp" in payload


@pytest.mark.asyncio
async def test_login_invalid_credentials_format(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "bad@example.com", "username": "baduser", "password": "pass1234"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "bad@example.com", "password": "wrong"},
    )
    assert response.status_code == 401
    payload = response.json()
    assert "detail" in payload
    assert "code" in payload
    assert "timestamp" in payload


@pytest.mark.asyncio
async def test_rate_limit_enforced():
    original_requests = settings.RATE_LIMIT_REQUESTS
    original_window = settings.RATE_LIMIT_WINDOW
    settings.RATE_LIMIT_REQUESTS = 1
    settings.RATE_LIMIT_WINDOW = 60
    app = create_application()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as session:
        first = await session.get("/health")
        second = await session.get("/health")
    settings.RATE_LIMIT_REQUESTS = original_requests
    settings.RATE_LIMIT_WINDOW = original_window
    assert first.status_code == 200
    assert second.status_code == 429
