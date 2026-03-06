import io

import pytest


@pytest.mark.asyncio
async def test_local_archive_roundtrip(tmp_path, monkeypatch):
    from mcp_agentskills.config import settings as settings_module

    settings_module.settings.SKILL_STORAGE_PATH = str(tmp_path)
    settings_module.settings.SKILL_ARCHIVE_BACKEND = "local"
    from mcp_agentskills.core.utils.skill_archive import load_archive, save_archive

    payload = b"zip-content"
    await save_archive("user-1", "skill-1", "1.0.0", payload)
    loaded = await load_archive("user-1", "skill-1", "1.0.0")
    assert loaded == payload


@pytest.mark.asyncio
async def test_s3_archive_roundtrip(monkeypatch):
    from mcp_agentskills.config import settings as settings_module

    settings_module.settings.SKILL_ARCHIVE_BACKEND = "s3"
    settings_module.settings.SKILL_ARCHIVE_S3_BUCKET = "bucket"
    settings_module.settings.SKILL_ARCHIVE_S3_ENDPOINT = "https://s3.test"
    settings_module.settings.SKILL_ARCHIVE_S3_ACCESS_KEY_ID = "key"
    settings_module.settings.SKILL_ARCHIVE_S3_SECRET_ACCESS_KEY = "secret"
    from mcp_agentskills.core.utils import skill_archive

    stored = io.BytesIO()

    class FakeClient:
        def put_object(self, Bucket, Key, Body):
            stored.seek(0)
            stored.truncate(0)
            stored.write(Body)

        def get_object(self, Bucket, Key):
            stored.seek(0)
            return {"Body": io.BytesIO(stored.read())}

    monkeypatch.setattr(skill_archive, "_get_s3_client", lambda: FakeClient())

    payload = b"s3-content"
    await skill_archive.save_archive("user-2", "skill-2", "2.0.0", payload)
    loaded = await skill_archive.load_archive("user-2", "skill-2", "2.0.0")
    assert loaded == payload
