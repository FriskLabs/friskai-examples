from typing import Literal

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Command, interrupt
from frisk_sdk.adapters.langchain import FriskLangchain as Frisk

from llm import get_llm
from prompt import system_prompt
from tools import llm_tools


class MyAgentState(MessagesState):
    """Agent state: messages (from MessagesState) plus custom user metadata."""

    user_id: str
    redact_me: str


async def build_agent(
    frisk: Frisk,
    checkpointer: BaseCheckpointSaver,
    *,
    require_approval: bool = False,
):
    """Build a hand-rolled LangGraph ReAct agent instrumented with FriskAI.

    Tools are wrapped with ``frisk.wrap_tools`` so each tool call is captured in
    FriskAI telemetry, and the wrapped tools are bound to both the model and the
    ``ToolNode`` so the schemas line up.

    The ``checkpointer`` is supplied by the caller so it can own the backing
    store's lifecycle (e.g. an on-disk SQLite connection that must stay open for
    the duration of a run).

    When ``require_approval`` is set, a ``human_review`` node is inserted before
    the tools run. It calls ``interrupt()`` to pause the graph -- the checkpointer
    persists that paused state, so approval can be granted in a later run (even a
    separate process) by resuming with ``Command(resume=...)``.
    """
    wrapped_tools = await frisk.wrap_tools(llm_tools)
    model = get_llm().bind_tools(wrapped_tools)

    async def call_model(state: MyAgentState) -> dict:
        messages = [SystemMessage(content=system_prompt), *state["messages"]]
        response = await model.ainvoke(messages)
        return {"messages": [response]}

    def route_after_model(state: MyAgentState) -> str:
        """Route to tools (or the approval gate) when tool calls are requested."""
        last_message = state["messages"][-1]
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "human_review" if require_approval else "tools"
        return END

    async def human_review(state: MyAgentState) -> Command[Literal["tools", "model"]]:
        """Pause for human approval before running the requested tool call(s)."""
        last_message = state["messages"][-1]
        assert isinstance(last_message, AIMessage)

        # interrupt() raises to pause on first execution; on resume it returns
        # the value passed via Command(resume=...).
        decision = interrupt(
            {
                "question": "Approve these tool call(s)?",
                "tool_calls": [
                    {"name": tc["name"], "args": tc["args"]}
                    for tc in last_message.tool_calls
                ],
            }
        )

        if decision == "approve":
            return Command(goto="tools")

        # On rejection, every pending tool_call still needs a matching result,
        # so hand the model a denial for each and let it respond without them.
        denials = [
            ToolMessage(
                content="The user declined to run this tool.",
                tool_call_id=tc["id"],
                name=tc["name"],
            )
            for tc in last_message.tool_calls
        ]
        return Command(goto="model", update={"messages": denials})

    graph = StateGraph(MyAgentState)
    graph.add_node("model", call_model)
    graph.add_node("tools", ToolNode(wrapped_tools))

    graph.add_edge(START, "model")
    if require_approval:
        graph.add_node("human_review", human_review)
        graph.add_conditional_edges("model", route_after_model, ["human_review", END])
    else:
        graph.add_conditional_edges("model", route_after_model, ["tools", END])
    graph.add_edge("tools", "model")

    return graph.compile(checkpointer=checkpointer)
