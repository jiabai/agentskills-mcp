import json
from datetime import datetime, timezone

from flowllm.core.context import C
from flowllm.core.op import BaseAsyncToolOp
from flowllm.core.schema import ToolCall

from mcp_agentskills.core.metrics.tool_call_metrics import record_tool_call
from mcp_agentskills.core.utils.skill_storage import get_skill_versions_dir, tool_error_payload
from mcp_agentskills.core.utils.user_context import get_current_user_id
from mcp_agentskills.db.session import get_async_session
from mcp_agentskills.repositories.skill import SkillRepository
from mcp_agentskills.repositories.skill_version import SkillVersionRepository
from mcp_agentskills.services.skill import SkillService


def _format_time(value: datetime | None) -> str | None:
    if not value:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@C.register_op()
class SkillListResourceOp(BaseAsyncToolOp):
    def build_tool_call(self) -> ToolCall:
        return ToolCall(
            **{
                "name": "skill_list_resource",
                "description": "Return MCP skill://list resource payload.",
                "input_schema": {},
            },
        )

    async def async_execute(self):
        exception: Exception | None = None
        try:
            user_id = get_current_user_id()
            if not user_id:
                payload = {"contents": [{"uri": "skill://list", "mimeType": "application/json", "text": '{"skills": []}'}]}
                self.set_output(json.dumps(payload, ensure_ascii=False))
                return
            async for session in get_async_session():
                skill_repo = SkillRepository(session)
                version_repo = SkillVersionRepository(session)
                skills = await skill_repo.list_by_user(user_id, include_inactive=False)
                items = []
                for skill in skills:
                    version = skill.current_version
                    if not version:
                        versions = await version_repo.list_by_skill(skill.id)
                        if versions:
                            version = versions[0].version
                    items.append(
                        {
                            "skill_id": skill.id,
                            "name": skill.name,
                            "version": version,
                            "description": skill.description,
                            "author": str(skill.user_id),
                            "visible": "private",
                            "created_at": _format_time(skill.created_at),
                            "updated_at": _format_time(skill.updated_at),
                            "tags": skill.tags,
                        }
                    )
                body = json.dumps({"skills": items}, ensure_ascii=False)
                payload = {"contents": [{"uri": "skill://list", "mimeType": "application/json", "text": body}]}
                self.set_output(json.dumps(payload, ensure_ascii=False))
                return
        except Exception as exc:
            exception = exc
            raise
        finally:
            await record_tool_call(
                "skill_list_resource",
                output=getattr(self, "_output", None),
                exception=exception,
            )


@C.register_op()
class SkillDetailResourceOp(BaseAsyncToolOp):
    def build_tool_call(self) -> ToolCall:
        return ToolCall(
            **{
                "name": "skill_detail_resource",
                "description": "Return MCP skill://{id}@{version} resource payload.",
                "input_schema": {
                    "skill_id": {"type": "string", "description": "Skill ID", "required": True},
                    "version": {"type": "string", "description": "Skill version", "required": False},
                },
            },
        )

    async def async_execute(self):
        exception: Exception | None = None
        try:
            user_id = get_current_user_id()
            if not user_id:
                self.set_output(tool_error_payload("Unauthorized", "UNAUTHORIZED"))
                return
            skill_id = self.input_dict["skill_id"]
            version_input = self.input_dict.get("version")
            async for session in get_async_session():
                skill_repo = SkillRepository(session)
                version_repo = SkillVersionRepository(session)
                skill = await skill_repo.get_by_id(skill_id)
                if not skill or str(skill.user_id) != str(user_id):
                    self.set_output(tool_error_payload("Skill not found", "SKILL_NOT_FOUND"))
                    return
                version = version_input or skill.current_version or ""
                if not version:
                    versions = await version_repo.list_by_skill(skill.id)
                    if versions:
                        version = versions[0].version
                if not version:
                    self.set_output(tool_error_payload("Version not found", "VERSION_NOT_FOUND"))
                    return
                record = await version_repo.get_by_version(skill.id, version)
                if not record:
                    self.set_output(tool_error_payload("Version not found", "VERSION_NOT_FOUND"))
                    return
                version_dir = get_skill_versions_dir(user_id, skill.name) / version
                skill_md_path = version_dir / "SKILL.md"
                metadata = {}
                if skill_md_path.exists():
                    content = skill_md_path.read_text(encoding="utf-8", errors="replace")
                    metadata = SkillService._parse_frontmatter(content)
                parameters = metadata.get("parameters")
                if isinstance(parameters, str):
                    try:
                        parameters = json.loads(parameters)
                    except Exception:
                        parameters = None
                detail = {
                    "skill_id": skill.id,
                    "version": version,
                    "name": metadata.get("name") or skill.name,
                    "description": metadata.get("description") or skill.description,
                    "author": str(skill.user_id),
                    "parameters": parameters,
                    "dependencies": list(record.dependencies or []),
                    "visible": "private",
                    "created_at": _format_time(skill.created_at),
                    "updated_at": _format_time(skill.updated_at),
                    "dependency_spec": record.dependency_spec or None,
                }
                body = json.dumps(detail, ensure_ascii=False)
                payload = {
                    "contents": [
                        {
                            "uri": f"skill://{skill.id}@{version}",
                            "mimeType": "application/json",
                            "text": body,
                        }
                    ]
                }
                self.set_output(json.dumps(payload, ensure_ascii=False))
                return
        except Exception as exc:
            exception = exc
            raise
        finally:
            await record_tool_call(
                "skill_detail_resource",
                output=getattr(self, "_output", None),
                exception=exception,
            )
