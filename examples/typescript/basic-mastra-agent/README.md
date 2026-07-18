# Basic Mastra Agent with FriskAI

This example demonstrates how to integrate FriskAI observability into an agent
built on **[Mastra](https://mastra.ai)**. It is the Mastra twin of the
`basic-langgraph-agent` (Python) example: same tools, same persistent multi-turn
conversation, same LLM provider matrix — but Mastra's `Agent` runs the ReAct loop
internally, so there is no hand-wired graph.

## Overview

The demo agent performs simple tasks using multiple tools:
- **Mathematical operations**: Add numbers together
- **Text analysis**: Count words in a string
- **File operations**: Read snippets from local files
- **Username lookup**: Returns a username for a user ID
- **Logging**: Logs a message to the console

## How it works

FriskAI's Mastra adapter integrates at three points:

- **Exporter** — `frisk.exporter()` is registered once on the `Mastra` instance's
  `Observability`, so every agent run emits telemetry to FriskAI.
- **Tool wrapping** — `frisk.wrapToolset()` instruments each tool to capture the
  model's reasoning for the call and returns the id-keyed record Mastra's
  `Agent.tools` expects.
- **Session** — `frisk.session({ threadId })` produces `tracingOptions` that are
  spread into each `agent.stream()` call to attach that run to a FriskAI session.

Conversation state is persisted with `@mastra/memory` backed by a LibSQL store on
disk (`memory.db`), keyed by a fixed thread id. A scripted 3-turn conversation
therefore continues across separate `bun run` invocations — turn 2 recalls turn
1's result, proving persistence.

> **Note:** The Mastra adapter provides telemetry and tool wrapping only. Policy
> enforcement (`guard()`) is **not** available for Mastra — see the
> `basic-langchain-agent` example for FriskAI policy enforcement.

## Features

### FriskAI Integration
- **Session Management**: A FriskAI session per turn
- **Tool Wrapping**: `frisk.wrapToolset` reasoning capture
- **Observability Exporter**: telemetry for every agent run
- **Data Redaction**: redact tool args (`path`) and agent state (`redactMe`)

### Mastra Components
- **Agent**: built-in ReAct loop with tool calling
- **Memory**: on-disk LibSQL store for multi-turn persistence
- **Multiple LLM Support**: OpenAI, Anthropic, Amazon Bedrock, or Ollama (via the
  Vercel AI SDK)

## Prerequisites

- [Bun](https://bun.sh/)
- FriskAI API key
- LLM provider credentials (OpenAI, Anthropic, AWS for Bedrock, or a local Ollama)

> **Note:** The Mastra adapter requires `@friskai/frisk-js` **>= 0.3.8** (the
> version that ships the `/mastra` export). This example depends on it as a
> normal npm range, just like the other examples.

## Setup

1. **Navigate to this example:**
   ```bash
   cd examples/typescript/basic-mastra-agent
   ```

2. **Install dependencies:**
   ```bash
   bun install
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```

   Edit `.env`:
   ```bash
   FRISK_API_KEY="your-frisk-api-key"

   # Set your LLM provider (openai, anthropic, bedrock, or ollama)
   LLM_PROVIDER="openai"
   OPENAI_API_KEY="your-openai-api-key"
   OPENAI_MODEL="gpt-5-nano"  # Optional
   ```

## Usage

Run the demo agent (advances one scripted turn per invocation):

```bash
bun run start
```

Run it three times to walk through the scripted conversation. Delete `memory.db`
to start over.

You can also pass a custom question (bypasses the script):

```bash
bun run start "Add 1 and 2, then count the words in 'hello there friend'."
```

## Project Structure

```
.
├── src/
│   ├── main.ts                      # Entry point: scripted persistent conversation
│   ├── agent.ts                     # Mastra instance (Frisk exporter) + Agent + Memory
│   ├── tools.ts                     # Tool definitions
│   ├── llm.ts                       # LLM provider selection
│   └── prompt.ts                    # System prompt
├── package.json
├── .env.example
└── README.md
```

## Learn More

- [FriskAI Documentation](https://docs.frisk.ai)
- [Mastra Documentation](https://mastra.ai/docs)
