import sys
import asyncio

from agentskills_mcp import AgentSkillsMcpApp
from agentskills_mcp.core.tools import LoadSkillMetadataOp

async def main(skill_dir: str):
    async with AgentSkillsMcpApp(
        f"metadata.skill_dir={skill_dir}"
    ):
        op = LoadSkillMetadataOp()
        await op.async_call()
        print(op.output) 


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: test_load_skill_metadata_op.py [skills directory]")
        sys.exit(1)
    skill_dir = sys.argv[1]
    asyncio.run(main(skill_dir))
