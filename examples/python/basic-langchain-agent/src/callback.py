from __future__ import annotations
from typing import Any

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.outputs.llm_result import LLMResult
from uuid import UUID


class CallbackHandler(BaseCallbackHandler):
    """A simple callback handler for langchain invoke callbacks that just prints out the events."""

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        inputs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        print(f"[Callback] Tool started: {kwargs['tool_call_id']}\n")

    def on_tool_end(
        self,
        output: ToolMessage,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> Any:
        print(f"[Callback] Tool ended: {output.tool_call_id}\n")

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        print("[Callback] LLM started\n")

    async def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        print(f"[Callback] LLM ended - {print_tool_calls_from_llm_result(response)}\n")


# function that takes in LLMResult, iterates through generations and prints tool call name and tool call id pairings.
def print_tool_calls_from_llm_result(llm_result: LLMResult) -> list[str]:
    """return dictionary of tool call name and tool call id pairings from LLMResult."""
    # result: dict[str,str] = {}
    result: list[str] = []
    for generation_list in llm_result.generations:
        for generation in generation_list:
            # check if generation is ChatGeneration to access message attribute
            if not hasattr(generation, "message"):
                continue
            message = generation.message  # type: ignore

            # check if message is BaseMessage to access tool_calls attribute
            if not isinstance(message, AIMessage):
                continue

            tool_calls = message.tool_calls
            for tool_call in tool_calls:
                tool_name = tool_call.get("name")
                tool_id = tool_call.get("id")
                result.append(f"{tool_name}:{tool_id}")
    return result
