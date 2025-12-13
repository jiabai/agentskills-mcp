import sys
import asyncio

from agentskills_mcp import AgentSkillsMcpApp
from agentskills_mcp.core.tools import LoadSkillMetadataOp, LoadSkillOp

async def main(skill_dir: str, skill_name: str):
    async with AgentSkillsMcpApp(
        f"metadata.skill_dir={skill_dir}"
    ):
        op = LoadSkillMetadataOp()
        await op.async_call()
        
        op = LoadSkillOp()
        await op.async_call(skill_name=skill_name)
        print(op.output)
        


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: test_load_skill_op.py [skills directory] [skill_name]")
        sys.exit(1)
    skill_dir = sys.argv[1]
    skill_name = sys.argv[2]
    asyncio.run(main(skill_dir, skill_name))
