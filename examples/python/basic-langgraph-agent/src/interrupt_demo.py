"""Human-in-the-loop interrupt/resume demo, persisted across processes.

The agent is built with ``require_approval=True``, so it pauses (via LangGraph's
``interrupt()``) before running any tool call. Because the on-disk SQLite
checkpointer saves that paused state, you approve or reject it in a *separate*
process run by resuming with ``Command(resume=...)``.

    python src/interrupt_demo.py            # turn 1: agent pauses awaiting approval
    python src/interrupt_demo.py approve    # resume and let the tool run
    python src/interrupt_demo.py reject     # (alternative) resume and deny the tool

Delete ``interrupt_checkpoints.sqlite`` to start the demo over.
"""

import os
import asyncio
from typing import Optional

from dotenv import load_dotenv
from frisk_sdk.adapters.langchain import FriskLangchain as Frisk
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.types import Command

from agent import build_agent

load_dotenv()

THREAD_ID = "approval_chat"
CHECKPOINT_DB = "interrupt_checkpoints.sqlite"

# A prompt that reliably triggers a tool call (log_message), so the approval
# gate has something to pause on.
INITIAL_PROMPT = (
    "Log the message 'shipping release v2 to production' using your logging tool."
)


class InterruptDemoRunner:
    def __init__(self) -> None:
        self.frisk = Frisk(
            api_key=os.getenv("FRISK_API_KEY", ""),
            redact={"redact_tool_args": ["path"], "redact_agent_state": ["redact_me"]},
        )

    async def run(self, *, arg: Optional[str] = None) -> None:
        async with AsyncSqliteSaver.from_conn_string(CHECKPOINT_DB) as saver:
            agent = await build_agent(
                frisk=self.frisk, checkpointer=saver, require_approval=True
            )
            config = {"configurable": {"thread_id": THREAD_ID}}

            state = await agent.aget_state(config)
            paused = bool(state.interrupts)

            frisk_session = self.frisk.session()
            stream_config = {"callbacks": [frisk_session.callbacks], **config}

            if paused:
                # A prior run stopped at the approval gate. The CLI arg is the
                # decision; default to approving.
                decision = (arg or "approve").lower()
                if decision not in ("approve", "reject"):
                    decision = "approve"
                print(f"--- Resuming paused run with decision: {decision.upper()} ---")
                stream_input = Command(resume=decision)
            else:
                # Fresh conversation. The CLI arg (if any) is a custom prompt.
                prompt = arg or INITIAL_PROMPT
                print(f"--- Starting approval conversation (thread '{THREAD_ID}') ---")
                print("User input:", prompt)
                stream_input = {
                    "messages": [HumanMessage(content=prompt)],
                    "user_id": "42",
                    "redact_me": "true",
                }

            print("\nLLM answer: ", end="", flush=True)
            async for event in agent.astream(
                stream_input,  # type: ignore
                config=stream_config,
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

            # Did we stop at an approval gate? If so, tell the user how to resume.
            state = await agent.aget_state(config)
            if state.interrupts:
                payload = state.interrupts[0].value
                print("\n[PAUSED] The agent wants to run these tool call(s):")
                for tc in payload.get("tool_calls", []):
                    print(f"  - {tc['name']}({tc['args']})")
                print(
                    "Run again to decide:\n"
                    "  python src/interrupt_demo.py approve\n"
                    "  python src/interrupt_demo.py reject"
                )

            self.frisk.shutdown()


if __name__ == "__main__":
    import sys

    arg = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(InterruptDemoRunner().run(arg=arg))
