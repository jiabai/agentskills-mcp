import os

import jwt
import pytest


@pytest.mark.asyncio
async def test_sso_login_creates_user_with_org_fields(client):
    payload = {
        "email": "sso@example.com",
        "username": "sso-user",
        "enterprise_id": "ent-1",
        "team_id": "team-1",
        "role": "admin",
        "status": "active",
        "iss": os.environ["SSO_JWT_ISSUER"],
        "aud": os.environ["SSO_JWT_AUDIENCE"],
    }
    token = jwt.encode(payload, os.environ["SSO_JWT_SECRET"], algorithm="HS256")
    response = await client.post("/api/v1/auth/sso/login", json={"id_token": token})
    assert response.status_code == 200
    access_token = response.json()["access_token"]
    me_response = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_response.status_code == 200
    data = me_response.json()
    assert data["enterprise_id"] == "ent-1"
    assert data["team_id"] == "team-1"
    assert data["role"] == "admin"
    assert data["status"] == "active"
