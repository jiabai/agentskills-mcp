
import asyncio

from skill_agent import SkillAgent

async def main():
    model_name = "qwen3-max"
    agent = SkillAgent(model_name=model_name, max_steps=50)

    # Run the ReAct loop with Agent Skills.
    query = "Fill Sample-Fillable-PDF.pdf with: name='Alice Johnson', select first choice from dropdown, check options 1 and 3, dependent name='Bob Johnson', age='12'. Save as filled-sample.pdf"
    messages = await agent.run(query)
    
    logger.info(f"result: {messages}")


if __name__ == "__main__":
    asyncio.run(main())
