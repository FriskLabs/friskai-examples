from dotenv import load_dotenv
import os
import asyncio
from agent import build_agent
from typing import Optional
from frisk_sdk.adapters.strands import Frisk

load_dotenv()

DEFAULT_PROMPT = (
    "Add 4.5 and 7.25. Count the words in "
    "'how many words are in this sentence?', show me the first few characters of agent.py, "
    "tell me the username for user ID 42 and then user ID 43,"
    "and log the message 'Looked up user by social security number 123-45-6789'."
)


async def demo_run(question: Optional[str] = None) -> None:
    frisk = Frisk(
        api_key=os.getenv("FRISK_API_KEY", ""),
        options={"redact_tool_args": ["path"], "redact_agent_state": ["redact_me"]},
    )
    frisk_session_id = frisk.create_session()

    """Run a demo interaction that forces the agent to use multiple tools."""
    agent = build_agent(frisk=frisk)
    user_input = question or DEFAULT_PROMPT
    print("User input:", user_input)
    print("\nAgent answer: ", end="", flush=True)

    agent_stream = agent.stream_async(
        user_input,
        invocation_state={
            "frisk_session_id": frisk_session_id,
            "redact_me": "This should be redacted in the logs",
            "user_id": "42",
        },
    )

    # Process events as they arrive
    async for event in agent_stream:
        if "data" in event:
            # Print text chunks as they're generated
            print(event["data"], end="", flush=True)

    frisk.shutdown()


if __name__ == "__main__":
    asyncio.run(demo_run())
