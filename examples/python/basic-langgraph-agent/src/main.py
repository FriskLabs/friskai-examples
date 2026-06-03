import os
import asyncio
from typing import Optional

from dotenv import load_dotenv
from frisk_sdk.adapters.langchain import FriskLangchain as Frisk
from langchain_core.messages import HumanMessage

from agent import build_agent

load_dotenv()

DEFAULT_PROMPT = (
    "Add 4.5 and 7.25. Count the words in "
    "'how many words are in this sentence?', show me the first few characters of agent.py, "
    "and tell me the username for user ID 42 and then user ID 43."
)


class DemoRunner:
    def __init__(self) -> None:
        self.frisk = Frisk(
            api_key=os.getenv("FRISK_API_KEY", ""),
            redact={"redact_tool_args": ["path"], "redact_agent_state": ["redact_me"]},
        )
        self.agent = asyncio.run(build_agent(frisk=self.frisk))

    async def run(self, *, question: Optional[str] = None) -> None:
        """Run a demo interaction that forces the LLM to use multiple tools."""
        user_input = question or DEFAULT_PROMPT
        print("User input:", user_input)
        print("\nLLM answer: ", end="", flush=True)

        agent_input = {
            "messages": [HumanMessage(content=user_input)],
            "user_id": "42",
            "redact_me": "true",
        }

        frisk_session = self.frisk.session()

        async for event in self.agent.astream(
            agent_input,  # type: ignore
            config={
                "callbacks": [frisk_session.callbacks],
                "configurable": {"thread_id": "in_memory_thread"},
            },
            stream_mode="messages",
        ):
            message, metadata = event
            if metadata.get("langgraph_node") == "model" and hasattr(message, "content"):
                content = message.content
                if isinstance(content, str) and content:
                    print(content, end="", flush=True)
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            print(item.get("text", ""), end="", flush=True)
        print()  # New line after streaming

        self.frisk.shutdown()


if __name__ == "__main__":
    import sys

    question = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(DemoRunner().run(question=question))
