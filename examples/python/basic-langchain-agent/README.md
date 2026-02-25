# Basic LangChain Agent with FriskAI

This example demonstrates how to integrate FriskAI observability into a LangChain agent application. It showcases key FriskAI features including tool wrapping, middleware, callback handlers, and data redaction.

## Overview

This demo agent performs simple tasks using multiple tools:
- **Mathematical operations**: Add numbers together
- **Text analysis**: Count words in a string
- **File operations**: Read snippets from local files

The agent is instrumented with FriskAI to provide full observability into tool calls, agent state, and execution flow.

## Features

### FriskAI Integration
- **Session Management**: Create and track agent sessions
- **Tool Wrapping**: Automatic instrumentation of LangChain tools
- **Tool Middleware**: Observe tool execution within the agent lifecycle
- **Callback Handler**: Capture LangChain events and metrics
- **Data Redaction**: Selectively redact sensitive information from tool arguments and agent state

### LangChain Components
- **Custom Agent State**: Extended state with user metadata
- **Multiple LLM Support**: OpenAI (GPT-4.1-nano) or Ollama (gpt-oss:20b)
- **Tool Calling**: Demonstrates multi-step tool usage

## Prerequisites

- Python 3.13
- [uv](https://docs.astral.sh/uv/) package manager
- FriskAI API key
- OpenAI API key (optional, falls back to Ollama)

## Setup

1. **Clone the repository and navigate to this example:**
   ```bash
   cd examples/python/basic-langchain-agent
   ```

2. **Install dependencies using uv:**
   ```bash
   uv sync
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your API keys:
   ```bash
   FRISK_API_KEY="your-frisk-api-key"
   OPENAI_API_KEY="your-openai-api-key"  # Optional
   ```

   Optional FriskAI configuration:
   ```bash
   FRISK_BASE_URL=""                    # Custom FriskAI endpoint
   FRISK_TOKEN_ISSUER_URL=""            # Custom token issuer
   FRISK_TELEMETRY_ENDPOINT=""          # Custom telemetry endpoint
   ```

## Usage

Run the demo agent:

```bash
uv run python src/main.py
```

This will execute a demo query that exercises multiple tools:
- Perform two addition operations
- Count words in a phrase
- Read the first few characters from a source file

### Example Output

```
Using OpenAI LLM as OPENAI_API_KEY is set.
User input:
 Add 4.5 and 7.25. Next, add 4.6 and 7.25, count the words in 'tool calling with langchain', and show me the first few characters of agent.py.

Final answer:
 [Agent response with tool results]
```

## Project Structure

```
.
├── src/
│   ├── main.py           # Entry point and demo runner
│   ├── agent.py          # Agent configuration with FriskAI
│   ├── tools.py          # Tool definitions (add, count, read)
│   ├── llm.py            # LLM provider selection
│   ├── prompt.py         # System prompt configuration
│   ├── callback.py       # Custom callback handlers
│   └── middleware.py     # Custom middleware
├── pyproject.toml        # Project dependencies
├── .env.example          # Environment template
└── README.md            # This file
```

## Key Code Examples

### Initializing FriskAI

```python
from frisk_sdk.adapters.langchain import Frisk

frisk = Frisk(
    api_key=os.getenv("FRISK_API_KEY", ""),
    options={
        "redact_tool_args": ['path'],      # Redact file paths
        "redact_agent_state": ["redact_me"] # Redact sensitive state
    }
)
frisk_session_id = frisk.create_session()
```

### Building the Agent

```python
agent = create_agent(
    model=get_llm(),
    tools=frisk.wrap_tools(llm_tools),        # Wrap tools for observability
    system_prompt=system_prompt,
    state_schema=MyAgentState,
    middleware=[frisk.tool_middleware()],      # Add FriskAI middleware
)
```

### Running with FriskAI

```python
result = agent.invoke(
    {
        "messages": [HumanMessage(content=user_input)],
        "user_id": "my_user_123",
        "redact_me": "true",
    },
    config={"callbacks": [frisk.callback_handler(session_id=frisk_session_id)]},
    context={"frisk_session_id": frisk_session_id},
)
```

## FriskAI Features Demonstrated

1. **Tool Wrapping**: `frisk.wrap_tools(llm_tools)` automatically instruments all tools
2. **Middleware**: `frisk.tool_middleware()` provides execution context
3. **Callbacks**: `frisk.callback_handler()` captures LangChain events
4. **Redaction**: Protect sensitive data in tool arguments and state

## Customization

### Adding New Tools

Add functions to `src/tools.py` and include them in the `llm_tools` list:

```python
def my_custom_tool(arg: str) -> str:
    """Description of what this tool does."""
    return f"Result: {arg}"

llm_tools = [add_numbers, word_count, read_snippet, my_custom_tool]
```

### Changing the LLM

Modify `src/llm.py` to use different models or providers. The example supports OpenAI and Ollama out of the box.

### Customizing Redaction

Update the `options` parameter when initializing Frisk:

```python
frisk = Frisk(
    api_key=api_key,
    options={
        "redact_tool_args": ['password', 'api_key', 'token'],
        "redact_agent_state": ["user_email", "sensitive_data"]
    }
)
```

## Learn More

- [FriskAI Documentation](https://docs.frisk.ai)
- [LangChain Documentation](https://python.langchain.com)
- [FriskAI SDK on PyPI](https://pypi.org/project/frisk-sdk/)

## Support

For questions about FriskAI integration or this example, please contact the FriskAI team or visit our documentation.
