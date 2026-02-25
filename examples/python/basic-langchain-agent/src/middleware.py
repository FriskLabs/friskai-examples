"""
LangChain middleware for logging tool calls.
"""

from langchain.agents.middleware import AgentMiddleware

from langchain.tools.tool_node import ToolCallRequest
from typing import Callable, Any


class ToolCallMiddleware(AgentMiddleware):
    """Middleware that logs tool call IDs."""

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Any],
    ) -> Any:
        print(f"[Middleware] Tool call ID: {request.tool_call['id']}\n")
        result = handler(request)
        return result
