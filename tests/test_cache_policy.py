import os

import jwt
import pytest


async def _sso_login(client, email, username, role="member"):
    payload = {
        "email": email,
        "username": username,
        "enterprise_id": "ent-cache",
        "team_id": "team-cache",
        "role": role,
        "status": "active",
        "iss": os.environ["SSO_JWT_ISSUER"],
        "aud": os.environ["SSO_JWT_AUDIENCE"],
    }
    token = jwt.encode(payload, os.environ["SSO_JWT_SECRET"], algorithm="HS256")
    response = await client.post("/api/v1/auth/sso/login", json={"id_token": token})
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_skill_cache_policy(client):
    token = await _sso_login(client, "cache@example.com", "cache-user")
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/skills/cache-policy", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert "cache_ttl_seconds" in payload
    assert "encryption_enabled" in payload
