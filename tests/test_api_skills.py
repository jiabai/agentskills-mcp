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
    payload = listed.json()
    assert payload["total"] == 1
    updated = await client.put(
        f"/api/v1/skills/{skill_id}",
        json={"description": "new"},
        headers=headers,
    )
    assert updated.status_code == 200
    deleted = await client.delete(f"/api/v1/skills/{skill_id}", headers=headers)
    assert deleted.status_code == 204


@pytest.mark.asyncio
async def test_skill_upload_and_list_files(client, tmp_path, monkeypatch):
    monkeypatch.setenv("SKILL_STORAGE_PATH", str(tmp_path))
    await client.post(
        "/api/v1/auth/register",
        json={"email": "upload@example.com", "username": "uploaduser", "password": "pass1234"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "upload@example.com", "password": "pass1234"},
    )
    access = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {access}"}
    created = await client.post(
        "/api/v1/skills",
        json={"name": "skillup", "description": "desc"},
        headers=headers,
    )
    skill_id = created.json()["id"]
    files = {"file": ("reference.md", b"hello", "text/markdown")}
    data = {"skill_id": skill_id}
    uploaded = await client.post("/api/v1/skills/upload", data=data, files=files, headers=headers)
    assert uploaded.status_code == 201
    listed = await client.get(f"/api/v1/skills/{skill_id}/files", headers=headers)
    assert listed.status_code == 200
    assert "reference.md" in listed.json()
    bad_files = {"file": ("../bad.txt", b"bad", "text/plain")}
    bad = await client.post("/api/v1/skills/upload", data=data, files=bad_files, headers=headers)
    assert bad.status_code == 400
