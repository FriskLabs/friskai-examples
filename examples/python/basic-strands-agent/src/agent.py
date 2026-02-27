from strands import Agent
from tools import tools
from llm import get_model
from prompt import system_prompt
from frisk_sdk.adapters.strands import Frisk


def build_agent(frisk: Frisk) -> Agent:
    """Build and return a Strands agent with custom tools and configuration."""
    agent = Agent(
        model=get_model(),
        tools=frisk.wrap_tools(tools),
        hooks=[frisk.tool_hook()],
        system_prompt=system_prompt,
        callback_handler=None,
    )
    return agent
