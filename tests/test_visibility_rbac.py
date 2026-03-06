import os

import jwt
import pytest


async def _sso_login(client, email, username, enterprise_id, team_id, role="member"):
    payload = {
        "email": email,
        "username": username,
        "enterprise_id": enterprise_id,
        "team_id": team_id,
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
async def test_skill_visibility_filters_list(client):
    token_owner = await _sso_login(client, "owner@example.com", "owner", "ent-1", "team-1", role="member")
    token_peer = await _sso_login(client, "peer@example.com", "peer", "ent-1", "team-1", role="member")
    token_other = await _sso_login(client, "other@example.com", "other", "ent-1", "team-2", role="member")

    headers_owner = {"Authorization": f"Bearer {token_owner}"}
    await client.post(
        "/api/v1/skills",
        json={"name": "enterprise-skill", "description": "desc", "visibility": "enterprise"},
        headers=headers_owner,
    )
    await client.post(
        "/api/v1/skills",
        json={"name": "team-skill", "description": "desc", "visibility": "team"},
        headers=headers_owner,
    )
    await client.post(
        "/api/v1/skills",
        json={"name": "private-skill", "description": "desc", "visibility": "private"},
        headers=headers_owner,
    )

    peer_response = await client.get("/api/v1/skills", headers={"Authorization": f"Bearer {token_peer}"})
    assert peer_response.status_code == 200
    peer_names = {item["name"] for item in peer_response.json()["items"]}
    assert "enterprise-skill" in peer_names
    assert "team-skill" in peer_names
    assert "private-skill" not in peer_names

    other_response = await client.get("/api/v1/skills", headers={"Authorization": f"Bearer {token_other}"})
    assert other_response.status_code == 200
    other_names = {item["name"] for item in other_response.json()["items"]}
    assert "enterprise-skill" in other_names
    assert "team-skill" not in other_names
    assert "private-skill" not in other_names
