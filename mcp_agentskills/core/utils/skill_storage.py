import re
from pathlib import Path

from mcp_agentskills.config.settings import settings

ALLOWED_EXTENSIONS = {".md", ".py", ".js", ".sh", ".txt", ".json", ".yaml", ".yml"}
SAFE_FILENAME_PATTERN = re.compile(r"^[a-zA-Z0-9_\-\.]+$")
MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_TOTAL_SIZE = 100 * 1024 * 1024
MAX_FILES_PER_SKILL = 50


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


def validate_filename(filename: str) -> tuple[bool, str]:
    if not filename or not filename.strip():
        return False, "Filename cannot be empty"
    if len(filename) > 255:
        return False, "Filename too long (max 255 characters)"
    if not SAFE_FILENAME_PATTERN.match(filename):
        return False, "Filename contains invalid characters"
    ext = Path(filename).suffix.lower()
    if ext and ext not in ALLOWED_EXTENSIONS:
        return False, f"File extension '{ext}' is not allowed"
    return True, "OK"


def validate_file_path(file_path: str) -> tuple[bool, str]:
    if not file_path or not file_path.strip():
        return False, "File path cannot be empty"
    if ".." in file_path:
        return False, "Path traversal detected: '..' is not allowed"
    if file_path.startswith("/") or (len(file_path) > 1 and file_path[1] == ":"):
        return False, "Absolute paths are not allowed"
    if "\\" in file_path:
        return False, "Backslashes are not allowed in file path"
    parts = file_path.split("/")
    for part in parts:
        if not part:
            continue
        if not SAFE_FILENAME_PATTERN.match(part):
            return False, f"Invalid filename component: '{part}'"
    ext = Path(file_path).suffix.lower()
    if ext and ext not in ALLOWED_EXTENSIONS:
        return False, f"File extension '{ext}' is not allowed"
    return True, "OK"


def get_safe_skill_path(base_dir: Path, user_id: str, skill_name: str, file_path: str) -> Path | None:
    base = base_dir / user_id / skill_name
    is_valid, _ = validate_file_path(file_path)
    if not is_valid:
        return None
    is_valid, _ = validate_file_path(skill_name)
    if not is_valid:
        return None
    target = (base / file_path).resolve()
    base_resolved = base.resolve()
    if not target.is_relative_to(base_resolved):
        return None
    return target
