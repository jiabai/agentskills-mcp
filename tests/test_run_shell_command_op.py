import sys
import asyncio

from agentskills_mcp import AgentSkillsMcpApp
from agentskills_mcp.core.tools import LoadSkillMetadataOp, RunShellCommandOp

async def main(skill_dir: str, skill_name: str, command: str):
    async with AgentSkillsMcpApp(
        f"metadata.skill_dir={skill_dir}"
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
    skill_dir = sys.argv[1]
    skill_name = sys.argv[2]
    command = sys.argv[3]
    asyncio.run(main(skill_dir, skill_name, command))
