# Basic Strands Agent

This example demonstrates how to build a simple AI agent using the Strands Agents SDK. It showcases key features including custom tools, multiple LLM providers, and streaming responses.

## Overview

This demo agent performs simple tasks using multiple tools:
- **Mathematical operations**: Add numbers together
- **Text analysis**: Count words in a string
- **File operations**: Read snippets from local files
- **Username lookup**: Returns username for a given user ID
- **Logging**: Log messages to the console

The agent uses the Strands Agents SDK for a simple, model-agnostic approach to building AI agents.

## Features

### Strands Agent Integration
- **Simple Agent Creation**: Build agents with just a few lines of code
- **Custom Tools**: Define tools using Python decorators
- **Multiple LLM Support**: OpenAI, Amazon Bedrock, Anthropic, or Ollama
- **Streaming Support**: Real-time streaming responses

## Prerequisites

- Python 3.13
- [uv](https://docs.astral.sh/uv/) package manager
- LLM provider credentials (OpenAI API key, AWS credentials for Bedrock, Anthropic API key, or local Ollama installation)

## Setup

1. **Clone the repository and navigate to this example:**
   ```bash
   cd examples/python/basic-strands-agent
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
   # Set your LLM provider (openai, bedrock, anthropic, or ollama)
   LLM_PROVIDER="openai"  # or "bedrock" or "anthropic" or "ollama"
   
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

## Usage

Run the demo agent:

```bash
uv run python src/main.py
```

This will execute a demo query that exercises multiple tools:
- Perform two addition operations
- Count words in a phrase
- Read the first few characters from a source file
- Look up usernames by user ID
- Log a message

### Example Output

```
Using OpenAI model (LLM_PROVIDER=openai).
User input: Add 4.5 and 7.25. Next, add 4.6 and 7.25, count the words in 'tool calling with strands', and show me the first few characters of agent.py.

Agent answer: [Agent response with tool results]
```

## Project Structure

```
.
├── src/
│   ├── main.py           # Entry point and demo runner
│   ├── agent.py          # Agent configuration
│   ├── tools.py          # Tool definitions (add, count, read, etc.)
│   ├── llm.py            # LLM provider selection
│   └── prompt.py         # System prompt configuration
├── pyproject.toml        # Project dependencies
├── .env.example          # Environment template
└── README.md            # This file
```

## Key Code Examples

### Building the Agent

```python
from strands import Agent
from tools import tools
from llm import get_model
from prompt import system_prompt

agent = Agent(
    model=get_model(),
    tools=tools,
    system_prompt=system_prompt,
)
```

### Running the Agent

```python
response = agent("Add 4.5 and 7.25")
print(response)
```

### Defining Custom Tools

```python
from strands import tool

@tool
def add_numbers(a: float, b: float) -> float:
    """Add two numbers and return the sum."""
    return a + b
```

## Customization

### Adding New Tools

Add functions to `src/tools.py` using the `@tool` decorator:

```python
from strands import tool

@tool
def my_custom_tool(arg: str) -> str:
    """Description of what this tool does."""
    return f"Result: {arg}"

tools = [add_numbers, word_count, read_snippet, my_custom_tool]
```

### Changing the LLM

Set the `LLM_PROVIDER` environment variable to choose your provider:
- `openai` - Uses OpenAI models (requires `OPENAI_API_KEY`)
- `bedrock` - Uses Amazon Bedrock models (requires AWS credentials)
- `anthropic` - Uses Anthropic models directly (requires `ANTHROPIC_API_KEY`)
- `ollama` - Uses local Ollama models (default if not specified)

You can also customize the specific model using provider-specific environment variables:
- OpenAI: `OPENAI_MODEL` (default: `gpt-5-nano`)
- Bedrock: `BEDROCK_MODEL_ID` (default: `qwen.qwen3-235b-a22b-2507-v1:0`)
- Anthropic: `ANTHROPIC_MODEL` (default: `claude-3-5-sonnet-20241022`)
- Ollama: `OLLAMA_MODEL` (default: `gpt-oss:20b`)

## Learn More

- [Strands Agents Documentation](https://strandsagents.com)
- [Strands Agents GitHub](https://github.com/strands-agents/sdk-python)
- [Strands Agents Samples](https://github.com/strands-agents/samples)

## Support

For questions about Strands Agents or this example, please visit the [Strands Agents GitHub repository](https://github.com/strands-agents/sdk-python).
