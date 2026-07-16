# Basic Mastra Agent Example — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `examples/typescript/basic-mastra-agent`, a Mastra-framework twin of `basic-langgraph-agent`, instrumented with the Frisk JS Mastra adapter (telemetry + tool wrapping + redaction), with on-disk LibSQL memory for a persistent scripted multi-turn conversation and a four-provider LLM matrix.

**Architecture:** Mastra's `Agent` runs the ReAct loop internally. Frisk integrates at three points: `frisk.exporter()` registered once on a `Mastra` instance's `Observability`; `frisk.wrapTools()` for per-tool reasoning capture; and `frisk.session({ threadId }).tracingOptions` spread into each `agent.stream()` call. Conversation state persists in a LibSQL store shared by the `Mastra` instance and the agent's `Memory`.

**Tech Stack:** TypeScript, Bun, Mastra (`@mastra/core`, `@mastra/memory`, `@mastra/libsql`, `@mastra/observability`), Vercel AI SDK providers (`@ai-sdk/openai`, `@ai-sdk/anthropic`, `@ai-sdk/amazon-bedrock`, `ollama-ai-provider-v2`), Zod, `@friskai/frisk-js/mastra`.

## Global Constraints

Every task's requirements implicitly include this section.

- **Package versions (exact floors, verified against installed packages):** `@friskai/frisk-js ^0.3.6` (resolves to 0.3.7, which has the `./mastra` export), `@mastra/core ^1.51.0`, `@mastra/memory ^1.23.0`, `@mastra/libsql ^1.16.0`, `@mastra/observability ^1.16.1`, `@ai-sdk/openai ^4.0.15`, `@ai-sdk/anthropic ^4.0.15`, `@ai-sdk/amazon-bedrock ^5.0.23`, `ollama-ai-provider-v2 ^4.0.1`, `zod ^4.4.3`.
- **Runtime:** Bun. `package.json` has `"type": "module"`, `"private": true`. Match the sibling `basic-langchain-agent` / `basic-claude-agent` structure and scripts (`start`, `lint`).
- **Module imports:** ESM with `.js` extensions on relative imports (matches sibling examples and `tsconfig` bundler mode). Frisk imported from `@friskai/frisk-js/mastra`.
- **Tools:** Mastra `Agent.tools` is a `Record<string, Tool>`, NOT an array — the array returned by `frisk.wrapTools()` MUST be converted to a record keyed by each tool's `id`.
- **Observability config:** the `Observability` instance config requires BOTH `name` and `serviceName` (a missing `serviceName` throws `OBSERVABILITY_INVALID_INSTANCE_CONFIG`).
- **No `guard()`:** Frisk's Mastra adapter provides no policy enforcement. Do not attempt to import or call `frisk.guard()`.
- **No unit tests:** these examples ship none (matches siblings and the spec). Per-task verification is `bunx tsc --noEmit` typecheck plus, where feasible, a runtime smoke; a final end-to-end run closes the plan.
- **Provider defaults (mirror the Python `llm.py`):** openai→`gpt-5-nano`, anthropic→`claude-3-5-sonnet-20241022`, bedrock→`qwen.qwen3-235b-a22b-2507-v1:0`, ollama→`gpt-oss:20b`.

## File Structure

| File | Responsibility |
|---|---|
| `package.json` | Deps, `start`/`lint` scripts. |
| `tsconfig.json`, `biome.json` | Copied verbatim from `basic-langchain-agent`. |
| `.gitignore` | Ignore `node_modules/` and `memory.db*`. |
| `.env.example` | Env template (same shape as the langchain example). |
| `.env` | Copied from `basic-langchain-agent/.env` (user request). |
| `src/tools.ts` | Five tools via `createTool`; exports `llmTools` (unwrapped array). |
| `src/prompt.ts` | Exports `systemPrompt`. |
| `src/llm.ts` | Exports `getModel()` — AI-SDK model by `LLM_PROVIDER`. |
| `src/agent.ts` | Exports `buildMastra(frisk)` → `{ agent, memory }`. Builds the Mastra instance (Frisk exporter + LibSQL storage) and the Agent (wrapped tools record + Memory). |
| `src/main.ts` | `DemoRunner` entrypoint: scripted 3-turn persistent conversation, turn counting, streamed output, Frisk session per turn. |
| `README.md` | Adapted from the langgraph README, with the "no guard() for Mastra" note. |

---

### Task 1: Scaffold project (config, env, deps)

**Files:**
- Create: `examples/typescript/basic-mastra-agent/package.json`
- Create: `examples/typescript/basic-mastra-agent/tsconfig.json`
- Create: `examples/typescript/basic-mastra-agent/biome.json`
- Create: `examples/typescript/basic-mastra-agent/.gitignore`
- Create: `examples/typescript/basic-mastra-agent/.env.example`
- Create: `examples/typescript/basic-mastra-agent/.env` (copied)

**Interfaces:**
- Produces: an installable project directory with all deps resolved; `bunx tsc --noEmit` runnable.

- [ ] **Step 1: Create `package.json`**

```json
{
  "name": "basic-mastra-agent",
  "version": "0.1.0",
  "description": "FriskAI basic Mastra agent example",
  "type": "module",
  "private": true,
  "scripts": {
    "start": "bun run src/main.ts",
    "lint": "biome check"
  },
  "devDependencies": {
    "@types/bun": "latest",
    "@biomejs/biome": "^2.4.4"
  },
  "peerDependencies": {
    "typescript": "^5"
  },
  "dependencies": {
    "@ai-sdk/amazon-bedrock": "^5.0.23",
    "@ai-sdk/anthropic": "^4.0.15",
    "@ai-sdk/openai": "^4.0.15",
    "@friskai/frisk-js": "^0.3.6",
    "@mastra/core": "^1.51.0",
    "@mastra/libsql": "^1.16.0",
    "@mastra/memory": "^1.23.0",
    "@mastra/observability": "^1.16.1",
    "ollama-ai-provider-v2": "^4.0.1",
    "zod": "^4.4.3"
  }
}
```

- [ ] **Step 2: Copy `tsconfig.json` and `biome.json` verbatim from the sibling**

```bash
cd examples/typescript/basic-mastra-agent
cp ../basic-langchain-agent/tsconfig.json ./tsconfig.json
cp ../basic-langchain-agent/biome.json ./biome.json
```

- [ ] **Step 3: Create `.gitignore`**

```
node_modules/
memory.db
memory.db-shm
memory.db-wal
```

- [ ] **Step 4: Create `.env.example`**

```
# FriskAI Configuration
FRISK_API_KEY=""
# FriskAI Configuration (Optional)
FRISK_BASE_URL=""
FRISK_TELEMETRY_ENDPOINT=""


# LLM Provider Configuration
LLM_PROVIDER=""  # Options: openai, bedrock, anthropic, ollama (defaults to ollama if not set)

# OpenAI Configuration
OPENAI_API_KEY=""
OPENAI_MODEL=""  # Optional, defaults to gpt-5-nano

# Amazon Bedrock Configuration
AWS_REGION=""  # e.g., us-east-1
AWS_ACCESS_KEY_ID=""
AWS_SECRET_ACCESS_KEY=""
BEDROCK_MODEL_ID=""  # Optional, defaults to qwen.qwen3-235b-a22b-2507-v1:0

# Anthropic Configuration
ANTHROPIC_API_KEY=""
ANTHROPIC_MODEL=""  # Optional, defaults to claude-3-5-sonnet-20241022

# Ollama Configuration
OLLAMA_MODEL=""  # Optional, defaults to gpt-oss:20b
```

- [ ] **Step 5: Copy the sibling `.env` (per user request)**

```bash
cd examples/typescript/basic-mastra-agent
cp ../basic-langchain-agent/.env ./.env
```

Note: this `.env` is the same already-tracked file the sibling example ships; it carries usable FriskAI + provider values so the example runs out of the box.

- [ ] **Step 6: Install dependencies**

Run: `cd examples/typescript/basic-mastra-agent && bun install`
Expected: all packages resolve; `bun.lock` created; no errors.

- [ ] **Step 7: Commit**

```bash
git add examples/typescript/basic-mastra-agent/package.json \
        examples/typescript/basic-mastra-agent/tsconfig.json \
        examples/typescript/basic-mastra-agent/biome.json \
        examples/typescript/basic-mastra-agent/.gitignore \
        examples/typescript/basic-mastra-agent/.env.example \
        examples/typescript/basic-mastra-agent/.env \
        examples/typescript/basic-mastra-agent/bun.lock
git commit -m "chore: scaffold basic-mastra-agent example"
```

---

### Task 2: Tools

**Files:**
- Create: `examples/typescript/basic-mastra-agent/src/tools.ts`

**Interfaces:**
- Produces: `export const llmTools` — an array of five Mastra `Tool` objects (created by `createTool`), each with a stable `id`. Consumed by `agent.ts` via `frisk.wrapTools(llmTools)`.

- [ ] **Step 1: Create `src/tools.ts`**

```typescript
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { createTool } from '@mastra/core/tools'
import { z } from 'zod'

export const lookupUsername = createTool({
  id: 'lookup_username',
  description: 'Function to look up a username by user ID.',
  inputSchema: z.object({
    userId: z.number().describe('The user ID to lookup'),
  }),
  execute: async ({ context }) => `user_${context.userId}`,
})

export const addNumbers = createTool({
  id: 'add_numbers',
  description: 'Add two numbers and return the sum.',
  inputSchema: z.object({
    a: z.number().describe('First number'),
    b: z.number().describe('Second number'),
  }),
  execute: async ({ context }) => context.a + context.b,
})

export const wordCount = createTool({
  id: 'word_count',
  description: 'Count the number of words in the provided text.',
  inputSchema: z.object({
    text: z.string().describe('The text to count words in'),
  }),
  execute: async ({ context }) =>
    context.text.split(/\s+/).filter((word) => word.length > 0).length,
})

export const readSnippet = createTool({
  id: 'read_snippet',
  description:
    'Read up to maxChars from a local file. Paths are resolved relative to src/.',
  inputSchema: z.object({
    path: z.string().describe('The file path relative to src/'),
    maxChars: z
      .number()
      .optional()
      .default(240)
      .describe('Maximum characters to read'),
  }),
  execute: async ({ context }) => {
    const maxCharacters = context.maxChars ?? 240
    const filePath = resolve(process.cwd(), 'src', context.path)
    try {
      const content = readFileSync(filePath, 'utf-8')
      return content.slice(0, maxCharacters) + (content.length > maxCharacters ? '...' : '')
    } catch {
      return `Error: File not found at path ${context.path}`
    }
  },
})

export const logMessage = createTool({
  id: 'log_message',
  description:
    'Log a message to the console (simulating an external logging tool).',
  inputSchema: z.object({
    message: z.string().describe('The message to log'),
  }),
  execute: async ({ context }) => {
    console.log(`LOG: ${context.message}`)
    return 'Message logged successfully.'
  },
})

export const llmTools = [
  lookupUsername,
  addNumbers,
  wordCount,
  readSnippet,
  logMessage,
]
```

- [ ] **Step 2: Typecheck**

Run: `cd examples/typescript/basic-mastra-agent && bunx tsc --noEmit`
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add examples/typescript/basic-mastra-agent/src/tools.ts
git commit -m "feat: add mastra tools"
```

---

### Task 3: System prompt

**Files:**
- Create: `examples/typescript/basic-mastra-agent/src/prompt.ts`

**Interfaces:**
- Produces: `export const systemPrompt: string`. Consumed by `agent.ts` as the Agent's `instructions`.

- [ ] **Step 1: Create `src/prompt.ts`** (copied verbatim from the Python `prompt.py`)

```typescript
export const systemPrompt =
  "You are my assistant. Provide a formatted paragraph response to the user's question." +
  "If you are unable to answer any or part of the question, just tell them that you don't have access to that information." +
  'If a policy restricts you, just move on to the next part of the question without mentioning the policy or that you are restricted. Do not mention anything about policies or restrictions.'
```

- [ ] **Step 2: Typecheck**

Run: `cd examples/typescript/basic-mastra-agent && bunx tsc --noEmit`
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add examples/typescript/basic-mastra-agent/src/prompt.ts
git commit -m "feat: add system prompt"
```

---

### Task 4: LLM provider selection

**Files:**
- Create: `examples/typescript/basic-mastra-agent/src/llm.ts`

**Interfaces:**
- Produces: `export function getModel()` — returns an AI-SDK language model chosen by `LLM_PROVIDER`. Consumed by `agent.ts` as the Agent's `model`.

- [ ] **Step 1: Create `src/llm.ts`**

```typescript
import { bedrock } from '@ai-sdk/amazon-bedrock'
import { anthropic } from '@ai-sdk/anthropic'
import { openai } from '@ai-sdk/openai'
import { createOllama } from 'ollama-ai-provider-v2'

export function getModel() {
  const provider = (process.env.LLM_PROVIDER || '').toLowerCase()

  if (provider === 'openai') {
    const model = process.env.OPENAI_MODEL || 'gpt-5-nano'
    console.log(`Using OpenAI LLM (LLM_PROVIDER=openai). Using model ${model}.`)
    return openai(model)
  }
  if (provider === 'bedrock') {
    const model =
      process.env.BEDROCK_MODEL_ID || 'qwen.qwen3-235b-a22b-2507-v1:0'
    console.log(
      `Using Amazon Bedrock LLM (LLM_PROVIDER=bedrock). Using model ${model}.`,
    )
    return bedrock(model)
  }
  if (provider === 'anthropic') {
    const model = process.env.ANTHROPIC_MODEL || 'claude-3-5-sonnet-20241022'
    console.log(
      `Using Anthropic LLM (LLM_PROVIDER=anthropic). Using model ${model}.`,
    )
    return anthropic(model)
  }
  const model = process.env.OLLAMA_MODEL || 'gpt-oss:20b'
  console.log(
    `LLM_PROVIDER not set or invalid. Defaulting to Ollama. Using model ${model}.`,
  )
  return createOllama()(model)
}
```

Notes: Bedrock reads `AWS_REGION` / `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` from the environment automatically. `getModel()` returns a union of the four provider model types; if the strict typechecker rejects assigning it to `Agent.model`, annotate the return as `import('@mastra/core/agent').MastraLanguageModel` — but the union is expected to be assignable (each provider model is individually accepted, verified against `@mastra/core@1.51.0`).

- [ ] **Step 2: Typecheck**

Run: `cd examples/typescript/basic-mastra-agent && bunx tsc --noEmit`
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add examples/typescript/basic-mastra-agent/src/llm.ts
git commit -m "feat: add LLM provider selection"
```

---

### Task 5: Agent + Mastra wiring

**Files:**
- Create: `examples/typescript/basic-mastra-agent/src/agent.ts`

**Interfaces:**
- Consumes: `getModel()` (llm.ts), `systemPrompt` (prompt.ts), `llmTools` (tools.ts), and a connected `Frisk` instance from `@friskai/frisk-js/mastra`.
- Produces: `export function buildMastra(frisk: Frisk): { agent: Agent; memory: Memory }`. `agent` is retrieved via `mastra.getAgent(AGENT_NAME)` so it is linked to the Mastra instance's observability. `memory` is the `Memory` instance (used by `main.ts` for turn counting). Exports `export const THREAD_ID` and `export const RESOURCE_ID`? No — those live in `main.ts`. This module owns only the Mastra/Agent/Memory build and the storage URL.

- [ ] **Step 1: Create `src/agent.ts`**

```typescript
import type { Frisk } from '@friskai/frisk-js/mastra'
import { Mastra } from '@mastra/core'
import type { Agent } from '@mastra/core/agent'
import { Agent as MastraAgent } from '@mastra/core/agent'
import { LibSQLStore } from '@mastra/libsql'
import type { Memory } from '@mastra/memory'
import { Memory as MastraMemory } from '@mastra/memory'
import { Observability } from '@mastra/observability'
import { getModel } from './llm.js'
import { systemPrompt } from './prompt.js'
import { llmTools } from './tools.js'

const AGENT_NAME = 'demoAgent'
const STORAGE_URL = 'file:./memory.db'

/**
 * Build a Mastra instance instrumented with the Frisk exporter, plus a ReAct
 * Agent with Frisk-wrapped tools and on-disk LibSQL memory.
 *
 * `wrapTools` returns an array; Mastra's `Agent.tools` is a record keyed by
 * tool id, so we convert. The agent is registered on the Mastra instance and
 * returned via `getAgent` so its runs flow through the Frisk exporter.
 */
export function buildMastra(frisk: Frisk): { agent: Agent; memory: Memory } {
  const storage = new LibSQLStore({ id: 'mastra-storage', url: STORAGE_URL })
  const memory = new MastraMemory({ storage, options: { lastMessages: 50 } })

  const wrappedTools = frisk.wrapTools(llmTools)
  const tools = Object.fromEntries(wrappedTools.map((tool) => [tool.id, tool]))

  const agent = new MastraAgent({
    id: AGENT_NAME,
    name: AGENT_NAME,
    instructions: systemPrompt,
    model: getModel(),
    tools,
    memory,
  })

  const mastra = new Mastra({
    agents: { [AGENT_NAME]: agent },
    storage,
    observability: new Observability({
      configs: {
        default: {
          name: 'default',
          serviceName: 'basic-mastra-agent',
          exporters: [frisk.exporter()],
        },
      },
    }),
  })

  return { agent: mastra.getAgent(AGENT_NAME), memory }
}
```

- [ ] **Step 2: Typecheck**

Run: `cd examples/typescript/basic-mastra-agent && bunx tsc --noEmit`
Expected: no errors. If `model: getModel()` fails to typecheck, apply the annotation from Task 4's note.

- [ ] **Step 3: Commit**

```bash
git add examples/typescript/basic-mastra-agent/src/agent.ts
git commit -m "feat: wire Mastra instance, Frisk exporter, and agent"
```

---

### Task 6: Main runner (scripted persistent conversation)

**Files:**
- Create: `examples/typescript/basic-mastra-agent/src/main.ts`

**Interfaces:**
- Consumes: `buildMastra(frisk)` (agent.ts), `Frisk` from `@friskai/frisk-js/mastra`, and `Memory` from `@mastra/memory` (type only).
- Produces: the runnable entrypoint (`bun run src/main.ts [question]`).

- [ ] **Step 1: Create `src/main.ts`**

```typescript
import { Frisk } from '@friskai/frisk-js/mastra'
import type { Memory } from '@mastra/memory'
import { buildMastra } from './agent.js'

// A fixed thread id plus an on-disk LibSQL store means every run continues the
// SAME conversation, even across separate processes.
const THREAD_ID = 'persistent_chat'
const RESOURCE_ID = 'user_42'

// Scripted turns that demonstrate memory carrying context forward. Turn 2 needs
// no tools and only succeeds if turn 1 was persisted; turn 3 combines recall
// (the earlier sum, the earlier user id) with fresh tool calls.
const SCRIPTED_TURNS = [
  'Add 4.5 and 7.25, and tell me the username for user ID 42.',
  'What was the sum you calculated, and which user ID did I ask about?',
  'Add 10 to that sum, and look up the username for the next user ID after the one I mentioned.',
]

/** Count human messages already persisted for the thread (0 if no thread yet). */
async function completedTurns(memory: Memory): Promise<number> {
  const thread = await memory.getThreadById({ threadId: THREAD_ID })
  if (!thread) {
    return 0
  }
  const { messages } = await memory.recall({
    threadId: THREAD_ID,
    resourceId: RESOURCE_ID,
    perPage: false,
  })
  return messages.filter((message) => message.role === 'user').length
}

async function run(question?: string): Promise<void> {
  const frisk = await Frisk.connect({
    apiKey: process.env.FRISK_API_KEY || '',
    redact: {
      redactToolArgs: ['path'],
      redactAgentState: ['redactMe'],
    },
  })

  try {
    const { agent, memory } = buildMastra(frisk)

    let userInput: string
    if (question !== undefined) {
      userInput = question
    } else {
      const turn = await completedTurns(memory)
      if (turn >= SCRIPTED_TURNS.length) {
        console.log(
          `Conversation complete (${turn} turns on thread '${THREAD_ID}'). ` +
            'Delete memory.db to start over.',
        )
        return
      }
      userInput = SCRIPTED_TURNS[turn]!
      console.log(
        `--- Turn ${turn + 1} of ${SCRIPTED_TURNS.length} (thread '${THREAD_ID}') ---`,
      )
    }

    console.log('User input:', userInput)
    process.stdout.write('\nLLM answer: ')

    const session = frisk.session({ threadId: THREAD_ID })
    const result = await agent.stream(userInput, {
      memory: { thread: THREAD_ID, resource: RESOURCE_ID },
      tracingOptions: session.tracingOptions,
    })

    for await (const chunk of result.textStream) {
      process.stdout.write(chunk)
    }
    console.log()
  } finally {
    frisk.shutdown()
  }
}

const question = process.argv.length > 2 ? process.argv[2] : undefined

await run(question)
```

- [ ] **Step 2: Typecheck**

Run: `cd examples/typescript/basic-mastra-agent && bunx tsc --noEmit`
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add examples/typescript/basic-mastra-agent/src/main.ts
git commit -m "feat: add scripted persistent-conversation runner"
```

---

### Task 7: README

**Files:**
- Create: `examples/typescript/basic-mastra-agent/README.md`

**Interfaces:**
- Produces: documentation. No code consumers.

- [ ] **Step 1: Create `README.md`**

````markdown
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
- **Tool wrapping** — `frisk.wrapTools()` instruments each tool to capture the
  model's reasoning for the call. (Mastra's `Agent.tools` is a record keyed by
  tool id, so the wrapped array is converted to a record.)
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
- **Tool Wrapping**: `frisk.wrapTools` reasoning capture
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
│   ├── main.ts     # Entry point: scripted persistent conversation
│   ├── agent.ts    # Mastra instance (Frisk exporter) + Agent + Memory
│   ├── tools.ts    # Tool definitions
│   ├── llm.ts      # LLM provider selection
│   └── prompt.ts   # System prompt
├── package.json
├── .env.example
└── README.md
```

## Learn More

- [FriskAI Documentation](https://docs.frisk.ai)
- [Mastra Documentation](https://mastra.ai/docs)
````

- [ ] **Step 2: Commit**

```bash
git add examples/typescript/basic-mastra-agent/README.md
git commit -m "docs: add basic-mastra-agent README"
```

---

### Task 8: End-to-end verification

**Files:** none (verification only).

- [ ] **Step 1: Lint**

Run: `cd examples/typescript/basic-mastra-agent && bun run lint`
Expected: biome reports no errors (fix formatting via `bunx biome check --write` if needed, then re-commit).

- [ ] **Step 2: Typecheck the whole project**

Run: `cd examples/typescript/basic-mastra-agent && bunx tsc --noEmit`
Expected: no errors.

- [ ] **Step 3: Run the scripted conversation end-to-end**

Ensure `.env` selects a provider whose credentials are valid (e.g. `LLM_PROVIDER=openai`).

Run (turn 1):
```bash
cd examples/typescript/basic-mastra-agent && rm -f memory.db memory.db-shm memory.db-wal && bun run start
```
Expected: prints `--- Turn 1 of 3 ...`, the user input, then a streamed answer that adds 4.5 + 7.25 (= 11.75) and reports `user_42`. A `memory.db` file is created.

Run (turn 2):
```bash
cd examples/typescript/basic-mastra-agent && bun run start
```
Expected: prints `--- Turn 2 of 3 ...` and a streamed answer that recalls the sum `11.75` and user ID `42` **with no new tool calls** — proving LibSQL persistence across processes.

Run (turn 3), then a fourth time:
```bash
cd examples/typescript/basic-mastra-agent && bun run start && bun run start
```
Expected: turn 3 answers (sum + 10 = 21.75, and `user_43`); the fourth run prints the "Conversation complete" message.

If network/credential limits in the current environment prevent the model or FriskAI calls from completing, verify as far as the environment allows (Frisk connect, Mastra/exporter construction, turn counting from persisted state) and record exactly which step could not be exercised.

- [ ] **Step 4: Confirm `memory.db` is gitignored**

Run: `cd examples/typescript/basic-mastra-agent && git status --porcelain`
Expected: no `memory.db*` files appear as untracked.

## Self-Review (completed during planning)

- **Spec coverage:** five tools (Task 2), scripted 3-turn persistence (Tasks 5–6), four providers (Task 4), redaction (Task 6), streamed output (Task 6), guard demo dropped with README note (Task 7) — all spec sections map to a task.
- **Placeholder scan:** every code step contains complete, executed-verified code; no TBD/TODO.
- **Type consistency:** `buildMastra(frisk) → { agent, memory }` produced in Task 5 and consumed in Task 6; `llmTools` produced in Task 2 and consumed in Task 5; `getModel()` produced in Task 4 and consumed in Task 5. Tool ids used to build the record match the `createTool` ids. `Memory.recall`/`getThreadById`, `agent.stream(...).textStream`, `session.tracingOptions`, `memory: { thread, resource }`, and `Observability` config (`name` + `serviceName` + `exporters`) were all verified against the installed `@mastra/core@1.51.0`, `@mastra/memory@1.23.0`, `@mastra/libsql@1.16.0`, and `@mastra/observability@1.16.1` during planning.
