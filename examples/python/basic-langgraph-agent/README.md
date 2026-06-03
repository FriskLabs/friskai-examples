# Basic LangGraph Agent with FriskAI

This example demonstrates how to integrate FriskAI observability into an agent
built directly on **LangGraph**. Instead of using `langchain.agents.create_agent`
(see the `basic-langchain-agent` example), the ReAct loop here is wired by hand
with a `StateGraph`, so you can see exactly how the model node, tool node, and
edges fit together.

## Overview

This demo agent performs simple tasks using multiple tools:
- **Mathematical operations**: Add numbers together
- **Text analysis**: Count words in a string
- **File operations**: Read snippets from local files
- **Username lookup**: Returns a username for a user ID
- **Logging**: Logs a message to the console

The agent is instrumented with FriskAI to provide observability into tool calls
and execution flow.

## How it works

The agent is a classic two-node ReAct loop compiled from a LangGraph `StateGraph`:

```
START → model → (tool calls?) → tools → model → … → END
```

- **`model` node** binds the FriskAI-wrapped tools to the LLM, prepends the
  system prompt, and produces the next assistant message.
- **Conditional edge** routes to the `tools` node when the model requested tool
  calls, otherwise ends the run.
- **`tools` node** is a LangGraph `ToolNode` that executes the requested tools
  and feeds the results back to the model.
- An `InMemorySaver` checkpointer (keyed by `thread_id`) holds conversation state.

## Features

### FriskAI Integration
- **Session Management**: Create and track an agent session
- **Tool Wrapping**: Automatic instrumentation of tools via `frisk.wrap_tools`
- **Callback Handler**: Capture agent events and tool-call telemetry
- **Data Redaction**: Selectively redact sensitive information from tool
  arguments and agent state

### LangGraph Components
- **Custom Agent State**: `MessagesState` extended with user metadata
- **Hand-built ReAct graph**: explicit `model` / `tools` nodes and edges
- **Multiple LLM Support**: OpenAI, Amazon Bedrock, Anthropic, or Ollama

## Prerequisites

- Python 3.13
- [uv](https://docs.astral.sh/uv/) package manager
- FriskAI API key
- LLM provider credentials (OpenAI API key, AWS credentials for Bedrock,
  Anthropic API key, or a local Ollama installation)

## Setup

1. **Navigate to this example:**
   ```bash
   cd examples/python/basic-langgraph-agent
   ```

2. **Install dependencies using uv:**
   ```bash
   uv sync
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and configure your LLM provider:
   ```bash
   FRISK_API_KEY="your-frisk-api-key"

   # Set your LLM provider (openai, bedrock, anthropic, or ollama)
   LLM_PROVIDER="openai"

   # For OpenAI
   OPENAI_API_KEY="your-openai-api-key"
   OPENAI_MODEL="gpt-5-nano"  # Optional, defaults to gpt-5-nano

   # For Amazon Bedrock
   AWS_REGION="us-east-1"
   AWS_ACCESS_KEY_ID="your-aws-access-key"
   AWS_SECRET_ACCESS_KEY="your-aws-secret-key"
   BEDROCK_MODEL_ID="qwen.qwen3-235b-a22b-2507-v1:0"  # Optional

   # For Anthropic
   ANTHROPIC_API_KEY="your-anthropic-api-key"
   ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"  # Optional

   # For Ollama
   OLLAMA_MODEL="gpt-oss:20b"  # Optional, defaults to gpt-oss:20b
   ```

   Optional FriskAI configuration:
   ```bash
   FRISK_BASE_URL=""                    # Custom FriskAI endpoint
   FRISK_TELEMETRY_ENDPOINT=""          # Custom telemetry endpoint
   ```

## Usage

Run the demo agent:

```bash
uv run python src/main.py
```

You can also pass a custom question:

```bash
uv run python src/main.py "Add 1 and 2, then count the words in 'hello there friend'."
```

## Project Structure

```
.
├── src/
│   ├── main.py           # Entry point and demo runner
│   ├── agent.py          # Hand-built StateGraph + FriskAI wiring
│   ├── tools.py          # Tool definitions
│   ├── llm.py            # LLM provider selection
│   └── prompt.py         # System prompt configuration
├── pyproject.toml        # Project dependencies
├── .env.example          # Environment template
└── README.md             # This file
```

## Key Code Examples

### Initializing FriskAI

```python
from frisk_sdk.adapters.langchain import FriskLangchain as Frisk

frisk = Frisk(
    api_key=os.getenv("FRISK_API_KEY", ""),
    redact={
        "redact_tool_args": ["path"],        # Redact file paths
        "redact_agent_state": ["redact_me"], # Redact sensitive state
    },
)
```

### Building the graph

```python
wrapped_tools = await frisk.wrap_tools(llm_tools)   # instrument tools
model = get_llm().bind_tools(wrapped_tools)

graph = StateGraph(MyAgentState)
graph.add_node("model", call_model)
graph.add_node("tools", ToolNode(wrapped_tools))
graph.add_edge(START, "model")
graph.add_conditional_edges("model", should_continue, ["tools", END])
graph.add_edge("tools", "model")
agent = graph.compile(checkpointer=InMemorySaver())
```

### Running with FriskAI

```python
frisk_session = frisk.session()

async for message, metadata in agent.astream(
    {
        "messages": [HumanMessage(content=user_input)],
        "user_id": "42",
        "redact_me": "true",
    },
    config={
        "callbacks": [frisk_session.callbacks],
        "configurable": {"thread_id": "in_memory_thread"},
    },
    stream_mode="messages",
):
    ...
```

## Customization

### Adding New Tools

Add functions to `src/tools.py` and include them in the `llm_tools` list:

```python
@tool
def my_custom_tool(arg: str) -> str:
    """Description of what this tool does."""
    return f"Result: {arg}"

llm_tools = [lookup_username, add_numbers, word_count, read_snippet, log_message, my_custom_tool]
```

### Changing the LLM

Set the `LLM_PROVIDER` environment variable to choose your provider:
- `openai` - Uses OpenAI models (requires `OPENAI_API_KEY`)
- `bedrock` - Uses Amazon Bedrock models (requires AWS credentials)
- `anthropic` - Uses Anthropic models directly (requires `ANTHROPIC_API_KEY`)
- `ollama` - Uses local Ollama models (default if not specified)

## Learn More

- [FriskAI Documentation](https://docs.frisk.ai)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [FriskAI SDK on PyPI](https://pypi.org/project/frisk-sdk/)

## Support

For questions about FriskAI integration or this example, please contact the
FriskAI team or visit our documentation.
