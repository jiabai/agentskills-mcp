import io
import zipfile

import pytest


@pytest.mark.asyncio
async def test_skill_lifecycle(client, tmp_path, monkeypatch):
    monkeypatch.setenv("SKILL_STORAGE_PATH", str(tmp_path))
    await client.post(
        "/api/v1/auth/verification-code",
        json={"email": "skill@example.com", "purpose": "register"},
    )
    await client.post(
        "/api/v1/auth/register",
        json={"email": "skill@example.com", "username": "skilluser", "code": "123456"},
    )
    await client.post(
        "/api/v1/auth/verification-code",
        json={"email": "skill@example.com", "purpose": "login"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "skill@example.com", "code": "123456"},
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
        json={"name": "skillx2", "description": "new"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "skillx2"
    deleted = await client.delete(f"/api/v1/skills/{skill_id}", headers=headers)
    assert deleted.status_code == 204


@pytest.mark.asyncio
async def test_skill_name_max_length(client):
    await client.post(
        "/api/v1/auth/verification-code",
        json={"email": "longskill@example.com", "purpose": "register"},
    )
    await client.post(
        "/api/v1/auth/register",
        json={"email": "longskill@example.com", "username": "longskill", "code": "123456"},
    )
    await client.post(
        "/api/v1/auth/verification-code",
        json={"email": "longskill@example.com", "purpose": "login"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "longskill@example.com", "code": "123456"},
    )
    access = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {access}"}
    long_name = "s" * 101
    response = await client.post(
        "/api/v1/skills",
        json={"name": long_name, "description": "desc"},
        headers=headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_skill_upload_and_list_files(client, tmp_path, monkeypatch):
    monkeypatch.setenv("SKILL_STORAGE_PATH", str(tmp_path))
    await client.post(
        "/api/v1/auth/verification-code",
        json={"email": "upload@example.com", "purpose": "register"},
    )
    await client.post(
        "/api/v1/auth/register",
        json={"email": "upload@example.com", "username": "uploaduser", "code": "123456"},
    )
    await client.post(
        "/api/v1/auth/verification-code",
        json={"email": "upload@example.com", "purpose": "login"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "upload@example.com", "code": "123456"},
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


@pytest.mark.asyncio
async def test_skill_zip_upload_creates_version(client, tmp_path, monkeypatch):
    monkeypatch.setenv("SKILL_STORAGE_PATH", str(tmp_path))
    await client.post(
        "/api/v1/auth/verification-code",
        json={"email": "zip@example.com", "purpose": "register"},
    )
    await client.post(
        "/api/v1/auth/register",
        json={"email": "zip@example.com", "username": "zipuser", "code": "123456"},
    )
    await client.post(
        "/api/v1/auth/verification-code",
        json={"email": "zip@example.com", "purpose": "login"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "zip@example.com", "code": "123456"},
    )
    access = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {access}"}
    created = await client.post(
        "/api/v1/skills",
        json={"name": "skillzip", "description": "desc"},
        headers=headers,
    )
    skill_id = created.json()["id"]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "SKILL.md",
            "---\nname: skillzip\ndescription: zip desc\nversion: 1.0.0\ndependencies: [dep1, dep2]\n---\nbody",
        )
        archive.writestr("reference.md", "hello")
    buffer.seek(0)
    files = {"file": ("skill.zip", buffer.read(), "application/zip")}
    data = {"skill_id": skill_id}
    uploaded = await client.post("/api/v1/skills/upload", data=data, files=files, headers=headers)
    assert uploaded.status_code == 201
    payload = uploaded.json()
    assert payload["version"] == "1.0.0"
    assert payload["current_version"] == "1.0.0"
    versions = await client.get(f"/api/v1/skills/{skill_id}/versions", headers=headers)
    assert versions.status_code == 200
    items = versions.json()["items"]
    assert items[0]["version"] == "1.0.0"
    assert items[0]["dependencies"] == ["dep1", "dep2"]
    listed = await client.get(f"/api/v1/skills/{skill_id}/files", headers=headers)
    assert "SKILL.md" in listed.json()
    assert "reference.md" in listed.json()


@pytest.mark.asyncio
async def test_skill_version_rollback_restores_files(client, tmp_path, monkeypatch):
    monkeypatch.setenv("SKILL_STORAGE_PATH", str(tmp_path))
    await client.post(
        "/api/v1/auth/verification-code",
        json={"email": "rollback@example.com", "purpose": "register"},
    )
    await client.post(
        "/api/v1/auth/register",
        json={"email": "rollback@example.com", "username": "rollback", "code": "123456"},
    )
    await client.post(
        "/api/v1/auth/verification-code",
        json={"email": "rollback@example.com", "purpose": "login"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "rollback@example.com", "code": "123456"},
    )
    access = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {access}"}
    created = await client.post(
        "/api/v1/skills",
        json={"name": "skillroll", "description": "desc"},
        headers=headers,
    )
    skill_id = created.json()["id"]
    first = io.BytesIO()
    with zipfile.ZipFile(first, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("SKILL.md", "---\nname: skillroll\nversion: 1.0.0\n---\nfirst")
    first.seek(0)
    await client.post(
        "/api/v1/skills/upload",
        data={"skill_id": skill_id},
        files={"file": ("skill.zip", first.read(), "application/zip")},
        headers=headers,
    )
    second = io.BytesIO()
    with zipfile.ZipFile(second, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("SKILL.md", "---\nname: skillroll\nversion: 1.1.0\n---\nsecond")
    second.seek(0)
    await client.post(
        "/api/v1/skills/upload",
        data={"skill_id": skill_id},
        files={"file": ("skill.zip", second.read(), "application/zip")},
        headers=headers,
    )
    rollback = await client.post(
        f"/api/v1/skills/{skill_id}/versions/1.0.0/rollback",
        headers=headers,
    )
    assert rollback.status_code == 200
    content = await client.get(
        f"/api/v1/skills/{skill_id}/files/SKILL.md",
        headers=headers,
    )
    assert "first" in content.text


@pytest.mark.asyncio
async def test_skill_deactivate_hides_from_list(client, tmp_path, monkeypatch):
    monkeypatch.setenv("SKILL_STORAGE_PATH", str(tmp_path))
    await client.post(
        "/api/v1/auth/verification-code",
        json={"email": "deactivate@example.com", "purpose": "register"},
    )
    await client.post(
        "/api/v1/auth/register",
        json={"email": "deactivate@example.com", "username": "deactivate", "code": "123456"},
    )
    await client.post(
        "/api/v1/auth/verification-code",
        json={"email": "deactivate@example.com", "purpose": "login"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "deactivate@example.com", "code": "123456"},
    )
    access = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {access}"}
    created = await client.post(
        "/api/v1/skills",
        json={"name": "skilldown", "description": "desc"},
        headers=headers,
    )
    skill_id = created.json()["id"]
    deactivated = await client.post(f"/api/v1/skills/{skill_id}/deactivate", headers=headers)
    assert deactivated.status_code == 200
    listed = await client.get("/api/v1/skills", headers=headers)
    assert listed.json()["total"] == 0
    listed_all = await client.get("/api/v1/skills?include_inactive=true", headers=headers)
    assert listed_all.json()["total"] == 1
    assert listed_all.json()["items"][0]["is_active"] is False
