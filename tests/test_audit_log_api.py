import os

import jwt
import pytest


async def _sso_login(client, email, username, role="admin"):
    payload = {
        "email": email,
        "username": username,
        "enterprise_id": "ent-audit",
        "team_id": "team-audit",
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
async def test_audit_log_query_and_export(client):
    token = await _sso_login(client, "audit@example.com", "auditor")
    headers = {"Authorization": f"Bearer {token}"}
    create_response = await client.post(
        "/api/v1/skills",
        json={"name": "audit-skill", "description": "desc", "visibility": "private"},
        headers=headers,
    )
    assert create_response.status_code == 201

    logs_response = await client.get("/api/v1/audit/logs", headers=headers)
    assert logs_response.status_code == 200
    items = logs_response.json()["items"]
    assert any(item["action"] == "skill.create" for item in items)

    export_response = await client.post(
        "/api/v1/audit/logs/export",
        json={"format": "json", "filters": {}},
        headers=headers,
    )
    assert export_response.status_code == 200
    payload = export_response.json()
    assert payload["format"] == "json"
    assert "content" in payload
