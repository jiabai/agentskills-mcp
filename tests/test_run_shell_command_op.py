"""Simple integration test for the RunShellCommandOp operator."""

import sys
import asyncio

from agentskills_mcp import AgentSkillsMcpApp
from agentskills_mcp.core.tools import LoadSkillMetadataOp, RunShellCommandOp


async def main(skill_dir: str, skill_name: str, command: str):
    """Execute the run_shell_command operation given a skill directory, a skill name, and a command."""
    async with AgentSkillsMcpApp(
        f"metadata.skill_dir={skill_dir}",
    ):
        op = LoadSkillMetadataOp()
        await op.async_call()

        op = RunShellCommandOp()
        await op.async_call(skill_name=skill_name, command=command)
        print(op.output)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: test_run_shell_command_op.py [skills directory] [skill_name] [command]")
        sys.exit(1)
    asyncio.run(main(sys.argv[1], sys.argv[2], sys.argv[3]))
