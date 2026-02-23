import pytest


@pytest.mark.asyncio
async def test_skill_lifecycle(client, tmp_path, monkeypatch):
    monkeypatch.setenv("SKILL_STORAGE_PATH", str(tmp_path))
    await client.post(
        "/api/v1/auth/register",
        json={"email": "skill@example.com", "username": "skilluser", "password": "pass1234"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "skill@example.com", "password": "pass1234"},
    )
    access = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {access}"}
    created = await client.post(
        "/api/v1/skills",
        json={"name": "skillx", "description": "desc"},
        headers=headers,
    )
    assert created.status_code == 201
    skill_id = created.json()["id"]
    listed = await client.get("/api/v1/skills", headers=headers)
    assert listed.status_code == 200
    updated = await client.patch(
        f"/api/v1/skills/{skill_id}",
        json={"description": "new"},
        headers=headers,
    )
    assert updated.status_code == 200
    deleted = await client.delete(f"/api/v1/skills/{skill_id}", headers=headers)
    assert deleted.status_code == 204
