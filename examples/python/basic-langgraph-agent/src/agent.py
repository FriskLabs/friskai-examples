from langchain_core.messages import AIMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from frisk_sdk.adapters.langchain import FriskLangchain as Frisk

from llm import get_llm
from prompt import system_prompt
from tools import llm_tools


class MyAgentState(MessagesState):
    """Agent state: messages (from MessagesState) plus custom user metadata."""

    user_id: str
    redact_me: str


def should_continue(state: MyAgentState) -> str:
    """Route to the tool node when the last message requested tool calls."""
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return END


async def build_agent(frisk: Frisk):
    """Build a hand-rolled LangGraph ReAct agent instrumented with FriskAI.

    Tools are wrapped with ``frisk.wrap_tools`` so each tool call is captured in
    FriskAI telemetry, and the wrapped tools are bound to both the model and the
    ``ToolNode`` so the schemas line up.
    """
    wrapped_tools = await frisk.wrap_tools(llm_tools)
    model = get_llm().bind_tools(wrapped_tools)

    async def call_model(state: MyAgentState) -> dict:
        messages = [SystemMessage(content=system_prompt), *state["messages"]]
        response = await model.ainvoke(messages)
        return {"messages": [response]}

    graph = StateGraph(MyAgentState)
    graph.add_node("model", call_model)
    graph.add_node("tools", ToolNode(wrapped_tools))

    graph.add_edge(START, "model")
    graph.add_conditional_edges("model", should_continue, ["tools", END])
    graph.add_edge("tools", "model")

    return graph.compile(checkpointer=InMemorySaver())
