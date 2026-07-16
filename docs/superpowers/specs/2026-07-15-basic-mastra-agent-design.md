# Basic Mastra Agent Example — Design

**Date:** 2026-07-15
**Status:** Approved

## Summary

Create a new TypeScript example, `examples/typescript/basic-mastra-agent`, that is
the Mastra-framework twin of the existing `examples/python/basic-langgraph-agent`.
It demonstrates integrating FriskAI observability into an agent built on
[Mastra](https://mastra.ai) using the Frisk JS Mastra adapter
(`@friskai/frisk-js/mastra`).

Where the langgraph example hand-wires a ReAct loop with a `StateGraph`, Mastra's
`Agent` runs that loop internally. Frisk integrates at the three points the adapter
exposes: an **exporter** (registered once on a `Mastra` instance's `Observability`),
**`wrapTools`** (reasoning capture per tool call), and **`session().tracingOptions`**
(attaches a run's telemetry to a Frisk session).

## Scope

**In scope** (parity with the langgraph example's core demo):

- Five tools: `lookupUsername`, `addNumbers`, `wordCount`, `readSnippet`, `logMessage`.
- Persistent, scripted **3-turn** conversation that survives across separate process
  runs (turn 2 recalls turn 1's result, proving persistence).
- Four LLM providers selected via `LLM_PROVIDER`: openai, anthropic, bedrock, ollama.
- Data redaction via Frisk (`redactToolArgs: ['path']`, `redactAgentState: ['redactMe']`).
- Streamed assistant output to the console.

**Out of scope** (and why):

- The **guard / human-in-the-loop interrupt** demo from the langgraph example.
  Frisk's Mastra adapter intentionally provides **no** `guard()` / policy enforcement
  (documented in the adapter README: *"The Mastra adapter provides telemetry and tool
  wrapping. Policy enforcement (`guard()`) is not available for Mastra."*). The example's
  README will state this and point readers at `basic-langchain-agent` for policy
  enforcement.
- Unit tests — these examples ship none.

## Architecture

```
main.ts ── DemoRunner
  ├─ Frisk.connect({ redact }) ────────── one-time
  ├─ new Mastra({ observability: { configs: {
  │       default: { name: 'default', exporters: [frisk.exporter()] } } } })
  ├─ new Agent({ model, instructions, tools: frisk.wrapTools(tools), memory })
  └─ per turn: agent.generate(input, {
  │       tracingOptions: session.tracingOptions,     // frisk.session({ threadId })
  │       memory: { thread, resource } })
```

The `Mastra` instance owns the Frisk exporter (one exporter per Frisk instance handles
every agent run). The `Agent` owns the wrapped tools and the memory store. Each turn
opens a fresh Frisk session and threads its `tracingOptions` into `agent.generate()`.

## File layout

Mirrors the sibling TypeScript examples (`basic-langchain-agent`, `basic-claude-agent`).

| File | Purpose |
|---|---|
| `src/tools.ts` | Five tools via `createTool` from `@mastra/core/tools`. |
| `src/llm.ts` | `getModel()` — selects an AI-SDK model from `LLM_PROVIDER`. |
| `src/prompt.ts` | System prompt (`instructions`), copied verbatim from the Python example. |
| `src/agent.ts` | Builds the `Mastra` instance (Frisk exporter) and the `Agent` (wrapped tools, LibSQL memory). Exports a builder used by `main.ts`. |
| `src/main.ts` | `DemoRunner`: scripted 3-turn persistent conversation; counts completed turns to pick the next one; streams the answer; opens a Frisk session per turn; CLI arg overrides with a freeform question. |
| `package.json` | `type: module`, `start: bun run src/main.ts`, `lint: biome check`. Deps: `@friskai/frisk-js`, `@mastra/core`, `@mastra/memory`, `@mastra/libsql`, `ai`, `@ai-sdk/openai`, `@ai-sdk/anthropic`, `@ai-sdk/amazon-bedrock`, `ollama-ai-provider`. |
| `tsconfig.json`, `biome.json` | Copied from a sibling TS example. |
| `.env.example` | Same shape as the langchain TS example's `.env.example`. |
| `.env` | Copied from `basic-langchain-agent/.env` so the example runs out of the box (per user request). |
| `README.md` | Adapted from the langgraph README: overview, Mastra wiring, the "no guard() for Mastra" note, setup/usage. |

## Key mechanics

### Persistence (mirrors the on-disk SQLite checkpointer)

- `Memory` from `@mastra/memory`, backed by `LibSQLStore` from `@mastra/libsql` at
  `file:./memory.db`, configured on the `Agent`.
- A fixed `thread` id and `resource` id key the conversation, so the 3 scripted turns
  persist across separate `bun run start` invocations.
- Turn selection: count prior user (human) messages persisted for the thread (analog of
  the Python `_completed_turns`) via Mastra's memory query API, and pick
  `SCRIPTED_TURNS[completed]`. When all turns are done, print a "conversation complete —
  delete memory.db to start over" message. A CLI argument overrides the script with a
  freeform follow-up.

The three scripted turns are carried over from the Python example (add two numbers +
look up a username; recall the sum and user id with no tools; add to that sum and look
up the next user id) — turn 2 only succeeds if turn 1 was persisted.

### Redaction

`Frisk.connect({ redact: { redactToolArgs: ['path'], redactAgentState: ['redactMe'] } })`
— same keys as the langgraph example. `readSnippet`'s `path` arg and a `redactMe` state
field are redacted from telemetry.

### Providers (Vercel AI SDK, which Mastra consumes)

`getModel()` reads `LLM_PROVIDER` and returns an AI-SDK model, matching the Python
`llm.py` defaults:

| Provider | Package | Default model |
|---|---|---|
| openai | `@ai-sdk/openai` | `gpt-5-nano` |
| anthropic | `@ai-sdk/anthropic` | `claude-3-5-sonnet-20241022` |
| bedrock | `@ai-sdk/amazon-bedrock` | `qwen.qwen3-235b-a22b-2507-v1:0` |
| ollama (default) | `ollama-ai-provider` | `gpt-oss:20b` |

## Verification

No unit tests. Verification is running the example end-to-end:

1. `bun install` in the example directory.
2. `bun run start` produces the streamed multi-turn conversation; turn 2 recalls turn
   1's sum (proving LibSQL persistence); a Frisk session is created per turn.
3. Re-running continues the same persisted conversation until all scripted turns are
   consumed.

If no provider credentials are available in the sandbox, drive the run far enough to
confirm wiring (Frisk connect, Mastra/exporter construction, memory persistence, turn
counting) and note the model-call step as unverified.

## Dependencies / open items

- Confirm the exact `@mastra/memory` query call used to count persisted user messages
  against the installed `@mastra/core ^1.51.0` line (the version Frisk JS peers on)
  during implementation; adjust the turn-counting helper accordingly.
