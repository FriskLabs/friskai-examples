from tools import llm_tools
from llm import get_llm
from prompt import system_prompt
from frisk_sdk.adapters.langchain import FriskLangchain as Frisk
from langchain.agents import create_agent, AgentState
from langgraph.checkpoint.memory import InMemorySaver


class MyAgentState(AgentState):
    user_id: str
    redact_me: str


async def build_agent(
    frisk: Frisk,
):
    agent = create_agent(
        model=get_llm(),
        tools=await frisk.wrap_tools(llm_tools),
        system_prompt=system_prompt,
        state_schema=MyAgentState,
        middleware=[frisk.guard()],
        checkpointer=InMemorySaver(),
    )
    return agent
