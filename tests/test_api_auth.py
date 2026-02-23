import pytest


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
