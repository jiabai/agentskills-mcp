from pathlib import Path

from mcp_agentskills.config.settings import settings


def _archive_key(user_id: str, skill_name: str, version: str) -> str:
    return f"{user_id}/{skill_name}/{version}.zip"


def _archive_path(user_id: str, skill_name: str, version: str) -> Path:
    base = Path(settings.SKILL_STORAGE_PATH) / "_archives" / user_id / skill_name
    return base / f"{version}.zip"


def _get_s3_client():
    import importlib

    boto3 = importlib.import_module("boto3")
    config_module = importlib.import_module("botocore.config")
    Config = getattr(config_module, "Config")
    session = boto3.session.Session()
    return session.client(
        "s3",
        region_name=settings.SKILL_ARCHIVE_S3_REGION or None,
        endpoint_url=settings.SKILL_ARCHIVE_S3_ENDPOINT or None,
        aws_access_key_id=settings.SKILL_ARCHIVE_S3_ACCESS_KEY_ID or None,
        aws_secret_access_key=settings.SKILL_ARCHIVE_S3_SECRET_ACCESS_KEY or None,
        config=Config(s3={"addressing_style": "path"})
        if settings.SKILL_ARCHIVE_S3_FORCE_PATH_STYLE
        else None,
    )


async def save_archive(user_id: str, skill_name: str, version: str, content: bytes) -> None:
    backend = (settings.SKILL_ARCHIVE_BACKEND or "local").lower()
    if backend == "s3":
        client = _get_s3_client()
        client.put_object(
            Bucket=settings.SKILL_ARCHIVE_S3_BUCKET,
            Key=_archive_key(user_id, skill_name, version),
            Body=content,
        )
        return
    path = _archive_path(user_id, skill_name, version)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


async def load_archive(user_id: str, skill_name: str, version: str) -> bytes | None:
    backend = (settings.SKILL_ARCHIVE_BACKEND or "local").lower()
    if backend == "s3":
        client = _get_s3_client()
        try:
            result = client.get_object(
                Bucket=settings.SKILL_ARCHIVE_S3_BUCKET,
                Key=_archive_key(user_id, skill_name, version),
            )
        except Exception:
            return None
        body = result.get("Body")
        return body.read() if body else None
    path = _archive_path(user_id, skill_name, version)
    if not path.exists():
        return None
    return path.read_bytes()
