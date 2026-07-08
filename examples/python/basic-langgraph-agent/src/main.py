import os
import asyncio
from typing import Optional

from dotenv import load_dotenv
from frisk_sdk.adapters.langchain import FriskLangchain as Frisk
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from agent import build_agent

load_dotenv()

# A fixed thread_id plus an on-disk checkpointer means every run of this script
# continues the SAME conversation, even across separate processes.
THREAD_ID = "persistent_chat"
CHECKPOINT_DB = "checkpoints.sqlite"

# Scripted turns that demonstrate the checkpointer carrying context forward.
# Turn 2 needs no tools and only succeeds if turn 1 was persisted; turn 3
# combines recall (the earlier sum, the earlier user ID) with fresh tool calls.
SCRIPTED_TURNS = [
    "Add 4.5 and 7.25, and tell me the username for user ID 42.",
    "What was the sum you calculated, and which user ID did I ask about?",
    "Add 10 to that sum, and look up the username for the next user ID after the one I mentioned.",
]


class DemoRunner:
    def __init__(self) -> None:
        self.frisk = Frisk(
            api_key=os.getenv("FRISK_API_KEY", ""),
            redact={"redact_tool_args": ["path"], "redact_agent_state": ["redact_me"]},
        )

    async def run(self, *, question: Optional[str] = None) -> None:
        """Run one turn of a persistent conversation.

        The agent is compiled with an on-disk SQLite checkpointer keyed by a
        fixed ``thread_id``. The saver holds an open connection, so it must live
        for the whole turn and share this coroutine's event loop -- hence the
        agent is built here rather than in ``__init__``.
        """
        async with AsyncSqliteSaver.from_conn_string(CHECKPOINT_DB) as saver:
            agent = await build_agent(frisk=self.frisk, checkpointer=saver)
            config = {"configurable": {"thread_id": THREAD_ID}}

            # A CLI argument overrides the script with a freeform follow-up.
            # Otherwise, pick the next scripted turn based on what's persisted.
            if question is not None:
                user_input = question
            else:
                turn = await self._completed_turns(agent, config)
                if turn >= len(SCRIPTED_TURNS):
                    print(
                        f"Conversation complete ({turn} turns on thread "
                        f"'{THREAD_ID}'). Delete {CHECKPOINT_DB} to start over."
                    )
                    self.frisk.shutdown()
                    return
                user_input = SCRIPTED_TURNS[turn]
                print(f"--- Turn {turn + 1} of {len(SCRIPTED_TURNS)} (thread '{THREAD_ID}') ---")

            print("User input:", user_input)
            print("\nLLM answer: ", end="", flush=True)

            agent_input = {
                "messages": [HumanMessage(content=user_input)],
                "user_id": "42",
                "redact_me": "true",
            }

            frisk_session = self.frisk.session()

            async for event in agent.astream(
                agent_input,  # type: ignore
                config={
                    "callbacks": [frisk_session.callbacks],
                    **config,
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

    async def _completed_turns(self, agent, config) -> int:
        """Count human messages already persisted for this thread."""
        state = await agent.aget_state(config)
        messages = state.values.get("messages", [])
        return sum(1 for m in messages if isinstance(m, HumanMessage))


if __name__ == "__main__":
    import sys

    question = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(DemoRunner().run(question=question))
