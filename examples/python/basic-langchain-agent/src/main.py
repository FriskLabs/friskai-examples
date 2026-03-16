import os
import time

from dotenv import load_dotenv
from frisk_sdk.adapters.langchain import Frisk
from langgraph.types import Command

from agent import build_agent
from langchain_core.messages import HumanMessage
from typing import Optional

load_dotenv()

DEFAULT_PROMPT = (
    "Add 4.5 and 7.25. Count the words in "
    "'how many words are in this sentence?', show me the first few characters of agent.py, "
    "tell me the username for user ID 42 and then user ID 43,"
    "and log the message 'Looked up user by social security number 123-45-6789'."
)

INTERRUPT_POLLING_INTERVAL_SECONDS = 5


class DemoRunner:
    def __init__(self) -> None:
        self.frisk = Frisk(
            api_key=os.getenv("FRISK_API_KEY", ""),
            redact={"redact_tool_args": ["path"], "redact_agent_state": ["redact_me"]},
        )
        self.agent = build_agent(frisk=self.frisk)

    def run(
        self,
        *,
        thread_id: str,
        question: Optional[str] = None,
        resume: Optional[Command] = None,
    ) -> None:
        """Run a demo interaction that forces the LLM to use multiple tools."""
        frisk_session = self.frisk.session()

        # Handle human-in-the-loop interrupts
        if resume:
            input = resume
            print("Retrying escalated tool calls...")
        else:
            user_input = question or DEFAULT_PROMPT
            print("User input:", user_input)
            print("\nLLM answer: ", end="", flush=True)
            input = {
                "messages": [HumanMessage(content=user_input)],
                "user_id": "42",
                "redact_me": "true",
            }

        next_resume = None
        for event in self.agent.stream(
            input,  # type: ignore
            config={"callbacks": [frisk_session.callbacks], "configurable": {"thread_id": thread_id}},
            context=frisk_session.context,  # type: ignore
            stream_mode=["messages", "updates"],
        ):
            stream_mode, chunk = event

            # Adjust this logic depending on the exact shape of your interrupt/update payloads
            if stream_mode == "updates":
                if isinstance(chunk, dict) and "__interrupt__" in chunk:
                    interrupt_data = chunk["__interrupt__"][0].value
                    if interrupt_data.get("__frisk"):
                        _message = interrupt_data.get("message", "")
                        escalated_tool_calls = interrupt_data.get("escalated_tool_calls", [])
                        next_resume = Command(
                            resume={tool_call_id: "retry" for tool_call_id in escalated_tool_calls.keys()} # Can simply pass in an empty dict here.
                        )

            elif stream_mode == "messages":
                message = chunk[0]
                metadata = chunk[1]
                if metadata.get("langgraph_node") == "model" and hasattr(message, "content"):
                    content = message.content
                    if isinstance(content, str) and content:
                        print(content, end="", flush=True)
                    elif isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "text":
                                print(item.get("text", ""), end="", flush=True)
        print()  # New line after streaming

        if next_resume:
            print(
                f"Some tool calls were escalated. Trying again in {INTERRUPT_POLLING_INTERVAL_SECONDS} seconds..."
            )
            time.sleep(INTERRUPT_POLLING_INTERVAL_SECONDS)
            self.run(resume=next_resume, thread_id=thread_id)
        else:
            self.frisk.shutdown()


def demo_run(*, question: Optional[str] = None, resume: Optional[Command] = None, thread_id: str) -> None:
    """Backward-compatible wrapper around DemoRunner."""
    DemoRunner().run(question=question, resume=resume, thread_id=thread_id)


if __name__ == "__main__":
    import sys

    question = None
    if len(sys.argv) > 1:
        question = sys.argv[1]
    demo_run(question=question, thread_id="in_memory_thread")
