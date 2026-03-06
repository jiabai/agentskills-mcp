import asyncio
import json
import os
from time import perf_counter

from flowllm.core.context import C
from flowllm.core.op import BaseAsyncToolOp
from flowllm.core.schema import ToolCall

from mcp_agentskills.core.metrics.tool_call_metrics import record_tool_call
from mcp_agentskills.core.security.rbac import has_permission, is_skill_visible
from mcp_agentskills.core.utils.command_whitelist import validate_command
from mcp_agentskills.core.utils.skill_storage import get_skill_versions_dir, tool_error_payload
from mcp_agentskills.core.utils.user_context import get_current_user_id
from mcp_agentskills.db import session as db_session
from mcp_agentskills.repositories.skill import SkillRepository
from mcp_agentskills.repositories.skill_version import SkillVersionRepository
from mcp_agentskills.repositories.user import UserRepository
from mcp_agentskills.services.skill import SkillService


def _entrypoint_to_command(entrypoint: str) -> str | None:
    lowered = entrypoint.lower()
    if lowered.endswith(".py"):
        return f"python {entrypoint}"
    if lowered.endswith(".js"):
        return f"node {entrypoint}"
    if lowered.endswith(".sh"):
        return f"bash {entrypoint}"
    return None


@C.register_op()
class ExecuteSkillOp(BaseAsyncToolOp):
    def build_tool_call(self) -> ToolCall:
        return ToolCall(
            **{
                "name": "execute_skill",
                "description": "Execute a skill from enterprise cloud",
                "input_schema": {
                    "skill_id": {"type": "string", "description": "Skill ID", "required": True},
                    "version": {"type": "string", "description": "Skill version", "required": False},
                    "parameters": {"type": "object", "description": "Skill parameters", "required": False},
                },
            },
        )

    def _set_output(self, value: str):
        self._output = value
        self.set_output(value)

    async def async_execute(self):
        exception: Exception | None = None
        try:
            self._output = None
            user_id = get_current_user_id()
            if not user_id:
                self._set_output(tool_error_payload("Unauthorized", "UNAUTHORIZED"))
                return
            skill_id = self.input_dict["skill_id"]
            version_input = self.input_dict.get("version")
            parameters = self.input_dict.get("parameters") or {}
            async for session in db_session.get_async_session():
                skill_repo = SkillRepository(session)
                version_repo = SkillVersionRepository(session)
                user_repo = UserRepository(session)
                user = await user_repo.get_by_id(user_id)
                if not user:
                    self._set_output(tool_error_payload("Unauthorized", "UNAUTHORIZED"))
                    return
                if not has_permission(user, "skill.execute"):
                    self._set_output(tool_error_payload("Permission denied", "PERMISSION_DENIED"))
                    return
                skill = await skill_repo.get_by_id(skill_id)
                if not skill or not is_skill_visible(user, skill):
                    self._set_output(tool_error_payload("Skill not found", "SKILL_NOT_FOUND"))
                    return
                if not skill.is_active:
                    self._set_output(tool_error_payload("Skill deactivated", "SKILL_DEACTIVATED"))
                    return
                version = version_input or skill.current_version or ""
                if not version:
                    versions = await version_repo.list_by_skill(skill.id)
                    if versions:
                        version = versions[0].version
                if not version:
                    self._set_output(tool_error_payload("Version not found", "VERSION_NOT_FOUND"))
                    return
                record = await version_repo.get_by_version(skill.id, version)
                if not record:
                    self._set_output(tool_error_payload("Version not found", "VERSION_NOT_FOUND"))
                    return
                version_dir = get_skill_versions_dir(user_id, skill.name) / version
                skill_md_path = version_dir / "SKILL.md"
                if not skill_md_path.exists():
                    self._set_output(tool_error_payload("SKILL.md not found", "SKILL_MD_NOT_FOUND"))
                    return
                content = skill_md_path.read_text(encoding="utf-8", errors="replace")
                metadata = SkillService._parse_frontmatter(content)
                command = metadata.get("command")
                if not command:
                    entrypoint = metadata.get("entrypoint")
                    if isinstance(entrypoint, str):
                        command = _entrypoint_to_command(entrypoint)
                if not command or not isinstance(command, str):
                    self._set_output(
                        tool_error_payload("Skill entrypoint not configured", "SKILL_EXECUTION_NOT_CONFIGURED")
                    )
                    return
                is_valid, error_msg = validate_command(command)
                if not is_valid:
                    self._set_output(tool_error_payload(error_msg, "COMMAND_BLOCKED"))
                    return
                env = os.environ.copy()
                env["SKILL_PARAMS"] = json.dumps(parameters, ensure_ascii=False)
                start = perf_counter()
                proc = await asyncio.create_subprocess_shell(
                    f"cd {version_dir} && {command}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env,
                )
                stdout, stderr = await proc.communicate()
                duration_ms = int((perf_counter() - start) * 1000)
                output = (stdout.decode(errors="replace") + stderr.decode(errors="replace")).strip()
                status = "success" if proc.returncode == 0 else "error"
                self._set_output(
                    json.dumps(
                        {"result": {"status": status, "output": output, "execution_time_ms": duration_ms}},
                        ensure_ascii=False,
                    )
                )
                return
        except Exception as exc:
            exception = exc
            raise
        finally:
            await record_tool_call(
                "execute_skill",
                output=getattr(self, "_output", None),
                exception=exception,
            )
