# FriskAI Examples

This repository contains example integrations and demos for **FriskAI**.

## About FriskAI

FriskAI provides real-time governance, human-in-the-loop control, and observability across agent actions. Key features include:

- **Session Tracking**: Monitor multi-turn conversations and agent executions
- **Tool Observability**: Automatic instrumentation of agent tools
- **Data Redaction**: Protect sensitive information in logs and traces
- **Performance Metrics**: Track latency, token usage, and costs
- **Debugging**: Inspect agent state, tool calls, and execution flow

## Examples

### Python

- **[Basic LangChain Agent](./examples/python/basic-langchain-agent/)** - A simple LangChain agent demonstrating FriskAI integration with tool wrapping, middleware, callbacks, and data redaction.
- **[Basic LangGraph Agent](./examples/python/basic-langgraph-agent/)** - A LangGraph agent with checkpointing and multi-turn support.
- **[Basic Strands Agent](./examples/python/basic-strands-agent/)** - A Strands agent with FriskAI integration.

### TypeScript

- **[Basic LangChain Agent](./examples/typescript/basic-langchain-agent/)** - A LangChain agent with FriskAI integration.
- **[Basic Claude Agent](./examples/typescript/basic-claude-agent/)** - A Claude Agent SDK agent with FriskAI integration.

## Getting Started

1. **Get a FriskAI API Key** - Contact the FriskAI team.

2. **Choose an example** - Navigate to the example directory that matches your framework

3. **Follow the setup instructions** - Each example includes a detailed README with installation and usage instructions

## Running examples from the repo root

Copy `.env.example` to `.env` and fill in your keys. The root `.env` is
injected verbatim into whichever example you run — except `FRISK_API_KEY`,
which is derived from `FRISK_API_KEY_LOCAL` / `FRISK_API_KEY_STAGING` /
`FRISK_API_KEY_PRODUCTION` based on `--frisk-env` (default: `local`). For
non-local environments, the matching entry in [`frisk-envs.json`](./frisk-envs.json)
overrides the `FRISK_BASE_URL` / `FRISK_TELEMETRY_ENDPOINT` from `.env`.

```bash
# <path> is relative to examples/: a directory runs src/main.py|.ts
# (or --example <name>); a file is executed directly.
./frisk-example.sh python/basic-langchain-agent
./frisk-example.sh python/basic-langgraph-agent --frisk-env staging --example interrupt_demo
./frisk-example.sh typescript/basic-claude-agent "any extra args are forwarded"
```

Python examples run via `uv run python`, TypeScript examples via `bun run`.

## Managing SDK versions

`set-versions.sh` pins the frisk SDK (`frisk-sdk` / `@friskai/frisk-js`) in one
or all examples and installs it:

```bash
./set-versions.sh                                              # all examples, versions from sdk-versions.txt
./set-versions.sh --example python/basic-langchain-agent --source-env local
```

`--source-env production` (default) reads registry versions from
[`sdk-versions.txt`](./sdk-versions.txt); `--source-env local` reads local SDK
checkout paths from `sdk-versions.local.txt` (copy
[`sdk-versions.local.example.txt`](./sdk-versions.local.example.txt) and point
it at your checkouts).

## Make targets

```bash
make run python/basic-langchain-agent                # alias for ./frisk-example.sh
make run -- python/basic-langchain-agent --frisk-env staging
make set-versions EXAMPLE=python/basic-langchain-agent SOURCE_ENV=local
make example -- python/basic-langchain-agent --frisk-env staging   # set-versions, then run
```

Words after `run` / `example` are forwarded to the script. The `--` is needed
before any `--flags` (make otherwise parses them as its own options);
multi-word quoted args need the `ARGS="..."` fallback. See `make help`.

## Requirements

Examples in this repository may require:
- Python 3.13+ and [uv](https://docs.astral.sh/uv/) (for Python examples)
- [Bun](https://bun.sh/) (for TypeScript examples)
- API keys for FriskAI and your chosen LLM provider

## Learn More

- [FriskAI SDK on PyPI](https://pypi.org/project/frisk-sdk/)
- [FriskAI SDK on npmjs](https://www.npmjs.com/package/@friskai/frisk-js)

## Support

For questions, issues, or feature requests, please contact the FriskAI team.
