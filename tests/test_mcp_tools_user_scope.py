import asyncio
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


def load_module(module_name: str, module_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def install_flowllm_stubs(skill_dir: Path):
    flowllm_module = ModuleType("flowllm")
    flowllm_core = ModuleType("flowllm.core")
    flowllm_context: Any = ModuleType("flowllm.core.context")
    flowllm_op: Any = ModuleType("flowllm.core.op")
    flowllm_schema: Any = ModuleType("flowllm.core.schema")

    class ServiceConfig:
        def __init__(self, dir_path: Path):
            self.metadata = {"skill_dir": str(dir_path)}

    class Context:
        def __init__(self, dir_path: Path):
            self.service_config = ServiceConfig(dir_path)

        def register_op(self):
            def decorator(cls):
                return cls

            return decorator

    class BaseAsyncToolOp:
        def __init__(self, **_kwargs):
            self.input_dict = {}
            self._output = None

        def set_output(self, output):
            self._output = output

        def get_prompt(self, _prompt_name: str):
            return "{skill_dir}"

    class ToolCall(dict):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

    flowllm_context.C = Context(skill_dir)
    flowllm_op.BaseAsyncToolOp = BaseAsyncToolOp
    flowllm_schema.ToolCall = ToolCall

    sys.modules["flowllm"] = flowllm_module
    sys.modules["flowllm.core"] = flowllm_core
    sys.modules["flowllm.core.context"] = flowllm_context
    sys.modules["flowllm.core.op"] = flowllm_op
    sys.modules["flowllm.core.schema"] = flowllm_schema

    return flowllm_context.C


def install_mcp_package_stubs(user_context_module, command_whitelist_module=None):
    mcp_agentskills = ModuleType("mcp_agentskills")
    mcp_agentskills.__path__ = []
    mcp_core = ModuleType("mcp_agentskills.core")
    mcp_core.__path__ = []
    mcp_utils = ModuleType("mcp_agentskills.core.utils")
    mcp_utils.__path__ = []

    sys.modules["mcp_agentskills"] = mcp_agentskills
    sys.modules["mcp_agentskills.core"] = mcp_core
    sys.modules["mcp_agentskills.core.utils"] = mcp_utils
    sys.modules["mcp_agentskills.core.utils.user_context"] = user_context_module
    if command_whitelist_module:
        sys.modules["mcp_agentskills.core.utils.command_whitelist"] = command_whitelist_module


def write_skill(base: Path, skill_name: str, description: str, body: str):
    skill_dir = base / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    content = f"---\nname: {skill_name}\ndescription: {description}\n---\n{body}\n"
    (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")


def load_user_context():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "mcp_agentskills"
        / "core"
        / "utils"
        / "user_context.py"
    )
    return load_module("mcp_agentskills.core.utils.user_context", module_path)


def load_command_whitelist():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "mcp_agentskills"
        / "core"
        / "utils"
        / "command_whitelist.py"
    )
    return load_module("mcp_agentskills.core.utils.command_whitelist", module_path)


def test_load_skill_metadata_scopes_by_user_id(tmp_path):
    user_context = load_user_context()
    command_whitelist = load_command_whitelist()
    install_mcp_package_stubs(user_context, command_whitelist)
    install_flowllm_stubs(tmp_path)

    write_skill(tmp_path, "global_skill", "global", "global body")
    write_skill(tmp_path / "user-1", "user_skill", "user", "user body")

    module_path = (
        Path(__file__).resolve().parents[1]
        / "mcp_agentskills"
        / "core"
        / "tools"
        / "load_skill_metadata_op.py"
    )
    module = load_module("mcp_agentskills.core.tools.load_skill_metadata_op", module_path)

    user_context.set_current_user_id("user-1")
    op = module.LoadSkillMetadataOp()
    asyncio.run(op.async_execute())
    assert "user_skill" in op._output
    assert "global_skill" not in op._output

    user_context.set_current_user_id(None)
    op = module.LoadSkillMetadataOp()
    asyncio.run(op.async_execute())
    assert "global_skill" in op._output


def test_load_skill_scopes_by_user_id(tmp_path):
    user_context = load_user_context()
    command_whitelist = load_command_whitelist()
    install_mcp_package_stubs(user_context, command_whitelist)
    install_flowllm_stubs(tmp_path)

    write_skill(tmp_path, "shared_skill", "global", "global body")
    write_skill(tmp_path / "user-2", "shared_skill", "user", "user body")

    module_path = (
        Path(__file__).resolve().parents[1]
        / "mcp_agentskills"
        / "core"
        / "tools"
        / "load_skill_op.py"
    )
    module = load_module("mcp_agentskills.core.tools.load_skill_op", module_path)

    user_context.set_current_user_id("user-2")
    op = module.LoadSkillOp()
    op.input_dict = {"skill_name": "shared_skill"}
    asyncio.run(op.async_execute())
    assert "user body" in op._output

    user_context.set_current_user_id(None)
    op = module.LoadSkillOp()
    op.input_dict = {"skill_name": "shared_skill"}
    asyncio.run(op.async_execute())
    assert "global body" in op._output


def test_read_reference_file_scopes_by_user_id(tmp_path):
    user_context = load_user_context()
    command_whitelist = load_command_whitelist()
    install_mcp_package_stubs(user_context, command_whitelist)
    install_flowllm_stubs(tmp_path)

    write_skill(tmp_path, "skill_x", "global", "global body")
    write_skill(tmp_path / "user-3", "skill_x", "user", "user body")

    (tmp_path / "skill_x" / "reference.md").write_text("global ref", encoding="utf-8")
    (tmp_path / "user-3" / "skill_x" / "reference.md").write_text("user ref", encoding="utf-8")

    module_path = (
        Path(__file__).resolve().parents[1]
        / "mcp_agentskills"
        / "core"
        / "tools"
        / "read_reference_file_op.py"
    )
    module = load_module("mcp_agentskills.core.tools.read_reference_file_op", module_path)

    user_context.set_current_user_id("user-3")
    op = module.ReadReferenceFileOp()
    op.input_dict = {"skill_name": "skill_x", "file_name": "reference.md"}
    asyncio.run(op.async_execute())
    assert op._output == "user ref"

    user_context.set_current_user_id(None)
    op = module.ReadReferenceFileOp()
    op.input_dict = {"skill_name": "skill_x", "file_name": "reference.md"}
    asyncio.run(op.async_execute())
    assert op._output == "global ref"


def test_run_shell_command_uses_user_scoped_workdir(tmp_path):
    user_context = load_user_context()
    command_whitelist = load_command_whitelist()
    install_mcp_package_stubs(user_context, command_whitelist)
    install_flowllm_stubs(tmp_path)

    write_skill(tmp_path, "skill_cmd", "global", "global body")
    write_skill(tmp_path / "user-4", "skill_cmd", "user", "user body")

    module_path = (
        Path(__file__).resolve().parents[1]
        / "mcp_agentskills"
        / "core"
        / "tools"
        / "run_shell_command_op.py"
    )
    module = load_module("mcp_agentskills.core.tools.run_shell_command_op", module_path)

    captured = {}

    async def fake_create_subprocess_shell(cmd, **_kwargs):
        captured["command"] = cmd

        class Proc:
            returncode = 0

            async def communicate(self):
                return b"ok", b""

        return Proc()

    module.asyncio.create_subprocess_shell = fake_create_subprocess_shell

    user_context.set_current_user_id("user-4")
    op = module.RunShellCommandOp(auto_install_deps=False)
    op.input_dict = {"skill_name": "skill_cmd", "command": "python -c \"print(1)\""}
    asyncio.run(op.async_execute())
    expected_dir = str(tmp_path / "user-4" / "skill_cmd")
    assert f"cd {expected_dir}" in captured["command"]
