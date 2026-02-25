from dataclasses import dataclass
from uuid_utils import UUID
from tools import llm_tools
from llm import get_llm
from prompt import system_prompt
from frisk_sdk.adapters.langchain import Frisk
from langchain.agents import create_agent, AgentState

class MyAgentState(AgentState):
    user_id: str
    redact_me: str

@dataclass
class CustomContext:
    frisk_session_id: UUID
    

def build_agent(
    frisk: Frisk,
):
    agent = create_agent(
        model=get_llm(),
        tools=frisk.wrap_tools(llm_tools),
        system_prompt=system_prompt,
        state_schema=MyAgentState,
        middleware=[frisk.tool_middleware()],
    )
    return agent
