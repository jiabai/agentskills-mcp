from pathlib import Path

from mcp_agentskills.config.settings import settings


def get_user_skill_dir(user_id: str, skill_name: str) -> Path:
    base = Path(settings.SKILL_STORAGE_PATH)
    return base / user_id / skill_name


def create_skill_dir(user_id: str, skill_name: str) -> Path:
    path = get_user_skill_dir(user_id, skill_name)
    path.mkdir(parents=True, exist_ok=True)
    return path


def delete_skill_dir(user_id: str, skill_name: str) -> None:
    path = get_user_skill_dir(user_id, skill_name)
    if not path.exists():
        return
    for child in path.rglob("*"):
        if child.is_file():
            child.unlink()
    for child in sorted(path.rglob("*"), reverse=True):
        if child.is_dir():
            child.rmdir()
    path.rmdir()


def save_file(user_id: str, skill_name: str, filename: str, content: bytes) -> Path:
    path = create_skill_dir(user_id, skill_name)
    file_path = path / filename
    file_path.write_bytes(content)
    return file_path


def list_files(user_id: str, skill_name: str) -> list[str]:
    path = get_user_skill_dir(user_id, skill_name)
    if not path.exists():
        return []
    return [str(item.relative_to(path)) for item in path.rglob("*") if item.is_file()]


def skill_exists(user_id: str, skill_name: str) -> bool:
    return get_user_skill_dir(user_id, skill_name).exists()
