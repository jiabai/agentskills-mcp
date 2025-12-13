import sys
import asyncio

from agentskills_mcp import AgentSkillsMcpApp
from agentskills_mcp.core.tools import LoadSkillMetadataOp, ReadReferenceFileOp

async def main(skill_dir: str, skill_name: str, file_name: str):
    async with AgentSkillsMcpApp(
        f"metadata.skill_dir={skill_dir}"
    ):
        op = LoadSkillMetadataOp()
        await op.async_call()
        
        op = ReadReferenceFileOp()
        await op.async_call(skill_name=skill_name, file_name=file_name)
        print(op.output)
        


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: test_reference_file_op.py [skills directory] [skill_name] [file_name]")
        sys.exit(1)
    skill_dir = sys.argv[1]
    skill_name = sys.argv[2]
    file_name = sys.argv[3]
    asyncio.run(main(skill_dir, skill_name, file_name))
