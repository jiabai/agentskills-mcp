from datetime import datetime, timezone
import difflib
import io
import json
from pathlib import Path
import re
import shutil
import zipfile

from mcp_agentskills.config.settings import settings
from mcp_agentskills.core.utils.skill_storage import (
    MAX_FILES_PER_SKILL,
    MAX_FILE_SIZE,
    MAX_TOTAL_SIZE,
    clear_skill_current_dir,
    create_skill_dir,
    delete_skill_dir,
    get_safe_skill_path,
    get_skill_versions_dir,
    get_user_skill_dir,
    list_files,
    validate_file_path,
    validate_skill_name,
    validate_filename,
)
from mcp_agentskills.models.skill import Skill
from mcp_agentskills.models.user import User
from mcp_agentskills.repositories.skill import SkillRepository
from mcp_agentskills.repositories.skill_version import SkillVersionRepository


class SkillService:
    def __init__(self, skill_repo: SkillRepository, version_repo: SkillVersionRepository | None = None):
        self.skill_repo = skill_repo
        self.version_repo = version_repo

    async def list_skills(
        self,
        user: User,
        skip: int = 0,
        limit: int = 100,
        query: str | None = None,
        include_inactive: bool = False,
    ) -> list[Skill]:
        return await self.skill_repo.list_by_user(
            user.id,
            skip=skip,
            limit=limit,
            query=query,
            include_inactive=include_inactive,
        )

    async def get_skill(self, user: User, skill_id: str) -> Skill:
        skill = await self.skill_repo.get_by_id(skill_id)
        if not skill or skill.user_id != user.id:
            raise ValueError("Skill not found")
        return skill

    async def create_skill(self, user: User, name: str, description: str) -> Skill:
        valid, error = validate_skill_name(name)
        if not valid:
            raise ValueError(error)
        if await self.skill_repo.get_by_name(user.id, name):
            raise ValueError("Skill already exists")
        path = create_skill_dir(user.id, name)
        return await self.skill_repo.create(
            user_id=user.id,
            name=name,
            description=description,
            skill_dir=str(path),
        )

    async def update_skill(self, user: User, skill_id: str, **fields) -> Skill:
        skill = await self.get_skill(user, skill_id)
        new_name = fields.get("name")
        if new_name is None:
            fields.pop("name", None)
        elif new_name != skill.name:
            valid, error = validate_skill_name(new_name)
            if not valid:
                raise ValueError(error)
            existing = await self.skill_repo.get_by_name(user.id, new_name)
            if existing and existing.id != skill.id:
                raise ValueError("Skill already exists")
            old_dir = get_user_skill_dir(user.id, skill.name)
            new_dir = get_user_skill_dir(user.id, new_name)
            if old_dir.exists():
                new_dir.parent.mkdir(parents=True, exist_ok=True)
                old_dir.rename(new_dir)
            else:
                new_dir.mkdir(parents=True, exist_ok=True)
            fields["skill_dir"] = str(new_dir)
        return await self.skill_repo.update(skill, **fields)

    async def deactivate_skill(self, user: User, skill_id: str) -> Skill:
        skill = await self.get_skill(user, skill_id)
        now = datetime.now(timezone.utc).replace(microsecond=0)
        return await self.skill_repo.update(skill, is_active=False, cache_revoked_at=now)

    async def activate_skill(self, user: User, skill_id: str) -> Skill:
        skill = await self.get_skill(user, skill_id)
        return await self.skill_repo.update(skill, is_active=True)

    async def delete_skill(self, user: User, skill_id: str) -> bool:
        skill = await self.get_skill(user, skill_id)
        await self.skill_repo.delete(skill)
        delete_skill_dir(user.id, skill.name)
        return True

    async def list_skill_files(self, user: User, skill_id: str) -> list[str]:
        skill = await self.get_skill(user, skill_id)
        return list_files(user.id, skill.name)

    async def read_skill_file(self, user: User, skill_id: str, file_path: str) -> str:
        skill = await self.get_skill(user, skill_id)
        base_dir = Path(settings.SKILL_STORAGE_PATH)
        safe_path = get_safe_skill_path(base_dir, user.id, skill.name, file_path)
        if not safe_path:
            raise ValueError("Invalid file path")
        if not safe_path.exists() or not safe_path.is_file():
            raise ValueError("File not found")
        return safe_path.read_text(encoding="utf-8", errors="replace")

    async def upload_file(self, user: User, skill_id: str, filename: str, content: bytes) -> str:
        skill = await self.get_skill(user, skill_id)
        valid, error = validate_filename(filename)
        if not valid:
            raise ValueError(error)
        if len(content) > MAX_FILE_SIZE:
            raise ValueError("File too large")
        existing = list_files(user.id, skill.name)
        if len(existing) >= MAX_FILES_PER_SKILL:
            raise ValueError("Too many files in skill")
        skill_dir = get_user_skill_dir(user.id, skill.name)
        total_size = 0
        for rel_path in existing:
            file_path = skill_dir / rel_path
            if file_path.exists() and file_path.is_file():
                total_size += file_path.stat().st_size
        if total_size + len(content) > MAX_TOTAL_SIZE:
            raise ValueError("Total skill size limit exceeded")
        base_dir = Path(settings.SKILL_STORAGE_PATH)
        safe_path = get_safe_skill_path(base_dir, user.id, skill.name, filename)
        if not safe_path:
            raise ValueError("Invalid file path")
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_bytes(content)
        return filename

    def _require_version_repo(self) -> SkillVersionRepository:
        if not self.version_repo:
            raise ValueError("Version repository not configured")
        return self.version_repo

    @staticmethod
    def _parse_frontmatter(content: str) -> dict:
        parts = content.split("---")
        if len(parts) < 3:
            return {}
        frontmatter_text = parts[1].strip()
        metadata: dict[str, object] = {}
        for line in frontmatter_text.split("\n"):
            line = line.strip()
            if not line or ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip().strip("\"'")
            if key == "dependencies":
                if value.startswith("[") and value.endswith("]"):
                    value = value[1:-1]
                deps = [item.strip().strip("\"'") for item in value.split(",") if item.strip()]
                metadata[key] = deps
            else:
                metadata[key] = value
        return metadata

    @staticmethod
    def _validate_version(version: str) -> str:
        normalized = str(version or "").strip()
        if not normalized:
            raise ValueError("Invalid version")
        if len(normalized) > 100:
            raise ValueError("Invalid version")
        if normalized.startswith("."):
            raise ValueError("Invalid version")
        if "/" in normalized or "\\" in normalized:
            raise ValueError("Invalid version")
        if ".." in normalized or normalized in {".", ".."}:
            raise ValueError("Invalid version")
        if not re.fullmatch(r"[a-zA-Z0-9_\-\.]+", normalized):
            raise ValueError("Invalid version")
        return normalized

    @staticmethod
    def _normalize_dependencies(value: object) -> list[str]:
        if isinstance(value, list):
            return [str(item) for item in value]
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return []

    async def list_versions(self, user: User, skill_id: str):
        repo = self._require_version_repo()
        skill = await self.get_skill(user, skill_id)
        return await repo.list_by_skill(skill.id)

    async def get_install_instructions(self, user: User, skill_id: str, version: str) -> dict:
        repo = self._require_version_repo()
        skill = await self.get_skill(user, skill_id)
        version = self._validate_version(version)
        record = await repo.get_by_version(skill.id, version)
        if not record:
            raise ValueError("Version not found")
        dependencies = list(record.dependencies or [])
        requirements_text = "\n".join(dependencies)
        commands: list[str] = []
        if dependencies:
            commands = [
                "pip install " + " ".join(dependencies),
                "pip install -r requirements.txt",
            ]
        return {
            "strategy": "client",
            "dependencies": dependencies,
            "requirements_text": requirements_text,
            "commands": commands,
        }

    async def diff_versions(self, user: User, skill_id: str, from_version: str, to_version: str) -> dict:
        skill = await self.get_skill(user, skill_id)
        base_dir = get_skill_versions_dir(user.id, skill.name)
        base_resolved = base_dir.resolve()
        from_version = self._validate_version(from_version)
        to_version = self._validate_version(to_version)
        from_dir = (base_dir / from_version).resolve()
        to_dir = (base_dir / to_version).resolve()
        if not from_dir.is_relative_to(base_resolved) or not to_dir.is_relative_to(base_resolved):
            raise ValueError("Invalid version")
        if not from_dir.exists() or not to_dir.exists():
            raise ValueError("Version files not found")
        from_files = {
            str(path.relative_to(from_dir)).replace("\\", "/")
            for path in from_dir.rglob("*")
            if path.is_file()
        }
        to_files = {str(path.relative_to(to_dir)).replace("\\", "/") for path in to_dir.rglob("*") if path.is_file()}
        added = sorted(to_files - from_files)
        removed = sorted(from_files - to_files)
        modified: list[dict] = []
        for relative in sorted(from_files & to_files):
            left = from_dir / relative
            right = to_dir / relative
            if left.read_bytes() == right.read_bytes():
                continue
            diff_text = ""
            if left.stat().st_size <= 100_000 and right.stat().st_size <= 100_000:
                left_text = left.read_text(encoding="utf-8", errors="replace").splitlines()
                right_text = right.read_text(encoding="utf-8", errors="replace").splitlines()
                diff_lines = difflib.unified_diff(
                    left_text,
                    right_text,
                    fromfile=f"{from_version}/{relative}",
                    tofile=f"{to_version}/{relative}",
                    lineterm="",
                )
                diff_text = "\n".join(diff_lines)
            modified.append({"path": relative, "diff": diff_text})
        return {
            "from_version": from_version,
            "to_version": to_version,
            "added": added,
            "removed": removed,
            "modified": modified,
        }

    async def rollback_version(self, user: User, skill_id: str, version: str):
        repo = self._require_version_repo()
        skill = await self.get_skill(user, skill_id)
        version = self._validate_version(version)
        record = await repo.get_by_version(skill.id, version)
        if not record:
            raise ValueError("Version not found")
        base_dir = get_skill_versions_dir(user.id, skill.name)
        base_resolved = base_dir.resolve()
        version_dir = (base_dir / version).resolve()
        if not version_dir.is_relative_to(base_resolved):
            raise ValueError("Invalid version")
        if not version_dir.exists():
            raise ValueError("Version files not found")
        clear_skill_current_dir(user.id, skill.name)
        root_dir = get_user_skill_dir(user.id, skill.name)
        for file_path in version_dir.rglob("*"):
            if not file_path.is_file():
                continue
            relative = file_path.relative_to(version_dir)
            target = root_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, target)
        await self.skill_repo.update(skill, current_version=version, description=record.description)
        return record

    async def upload_zip(
        self,
        user: User,
        skill_id: str,
        filename: str,
        content: bytes,
        metadata_text: str | None = None,
    ) -> dict:
        repo = self._require_version_repo()
        skill = await self.get_skill(user, skill_id)
        if not filename.lower().endswith(".zip"):
            raise ValueError("Invalid zip file")
        try:
            archive = zipfile.ZipFile(io.BytesIO(content))
        except zipfile.BadZipFile as exc:
            raise ValueError("Invalid zip file") from exc
        with archive:
            entries = [info for info in archive.infolist() if not info.is_dir()]
            if not entries:
                raise ValueError("Zip is empty")
            if len(entries) > MAX_FILES_PER_SKILL:
                raise ValueError("Too many files in skill")
            total_size = sum(info.file_size for info in entries)
            if total_size > MAX_TOTAL_SIZE:
                raise ValueError("Total skill size limit exceeded")
            for info in entries:
                if info.file_size > MAX_FILE_SIZE:
                    raise ValueError("File too large")
                file_path = info.filename.replace("\\", "/").lstrip("/")
                valid, error = validate_file_path(file_path)
                if not valid:
                    raise ValueError(error)
            skill_md = next(
                (info for info in entries if info.filename.replace("\\", "/").lstrip("/") == "SKILL.md"),
                None,
            )
            if not skill_md:
                raise ValueError("SKILL.md not found")
            skill_md_content = archive.read(skill_md).decode("utf-8", errors="replace")
            frontmatter = self._parse_frontmatter(skill_md_content)
            metadata: dict = {}
            if metadata_text:
                try:
                    parsed = json.loads(metadata_text)
                except json.JSONDecodeError as exc:
                    raise ValueError("Invalid metadata") from exc
                if isinstance(parsed, dict):
                    metadata = parsed
            version = str(metadata.get("version") or frontmatter.get("version") or "")
            if not version:
                version = datetime.now(timezone.utc).strftime("v%Y%m%d%H%M%S")
            version = self._validate_version(version)
            existing = await repo.get_by_version(skill.id, version)
            if existing:
                raise ValueError("Version already exists")
            description = str(metadata.get("description") or frontmatter.get("description") or skill.description)
            dependencies = self._normalize_dependencies(metadata.get("dependencies") or frontmatter.get("dependencies"))
            base_dir = get_skill_versions_dir(user.id, skill.name)
            base_resolved = base_dir.resolve()
            version_dir = (base_dir / version).resolve()
            if not version_dir.is_relative_to(base_resolved):
                raise ValueError("Invalid version")
            if version_dir.exists():
                raise ValueError("Version already exists")
            version_dir.mkdir(parents=True, exist_ok=True)
            for info in entries:
                file_path = info.filename.replace("\\", "/").lstrip("/")
                target = version_dir / file_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(info))
            clear_skill_current_dir(user.id, skill.name)
            root_dir = get_user_skill_dir(user.id, skill.name)
            for entry_path in version_dir.rglob("*"):
                if not entry_path.is_file():
                    continue
                relative = entry_path.relative_to(version_dir)
                target = root_dir / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(entry_path, target)
            record = await repo.create_version(
                skill_id=skill.id,
                version=version,
                description=description,
                dependencies=dependencies,
                metadata={
                    "name": metadata.get("name") or frontmatter.get("name") or skill.name,
                    "description": description,
                    "version": version,
                    "dependencies": dependencies,
                },
            )
            await self.skill_repo.update(skill, current_version=version, description=description, is_active=True)
            return {
                "version": record.version,
                "current_version": version,
                "dependencies": record.dependencies,
            }
