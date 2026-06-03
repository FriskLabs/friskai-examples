from strands import Agent
from tools import tools
from llm import get_model
from prompt import system_prompt
from frisk_sdk.adapters.strands import FriskStrands as Frisk


async def build_agent(frisk: Frisk) -> Agent:
    """Build and return a Strands agent with custom tools and configuration."""
    agent = Agent(
        model=get_model(),
        tools=await frisk.wrap_tools(tools),
        hooks=[frisk.guard()],
        system_prompt=system_prompt,
        callback_handler=None,
    )
    return agent
