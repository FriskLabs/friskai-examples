import os
from dotenv import load_dotenv
from frisk_sdk.adapters.langchain import Frisk
from agent import build_agent
from langchain_core.messages import HumanMessage
from typing import Optional

load_dotenv()

DEFAULT_PROMPT = (
    "Add 4.5 and 7.25. Count the words in "
    "'how many words are in this sentence?', show me the first few characters of agent.py, "
    "and tell me the username for user ID 42 and then user ID 43"
)


def demo_run(question: Optional[str] = None) -> None:
    """Run a demo interaction that forces the LLM to use multiple tools."""
    frisk = Frisk(
        api_key=os.getenv("FRISK_API_KEY", ""),
        options={"redact_tool_args": ["path"], "redact_agent_state": ["redact_me"]},
    )
    frisk_session_id = frisk.create_session()
    agent = build_agent(frisk=frisk)
    user_input = question or DEFAULT_PROMPT
    print("User input:", user_input)
    result = agent.invoke(
        {
            "messages": [HumanMessage(content=user_input)],
            "user_id": "42",
            "redact_me": "true",
        },  # type: ignore
        config={"callbacks": [frisk.callback_handler(session_id=frisk_session_id)]},
        context={"frisk_session_id": frisk_session_id},  # type: ignore
    )
    final_message = result["messages"][-1]
    print("\nLLM answer:", getattr(final_message, "content", final_message))
    frisk.shutdown()


if __name__ == "__main__":
    demo_run()
