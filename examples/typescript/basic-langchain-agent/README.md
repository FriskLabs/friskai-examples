# Basic LangChain Agent with FriskAI

A complete working example of a LangChain agent integrated with FriskAI. This example demonstrates how to build an AI agent with multiple tools and deploy it with real-time governance, control, and observability.

**About FriskAI**: FriskAI enables enterprises to deploy AI agents in high-stakes environments with confidence. Our platform provides real-time governance, control, and observability across agent tool calls.

## Overview

This example showcases a fully functional LangChain agent that uses multiple tools to complete complex tasks. The agent can:

- **Mathematical operations**: Add numbers together
- **Text analysis**: Count words in strings
- **File operations**: Read snippets from local files
- **User lookups**: Get usernames by user ID
- **Logging**: Output messages to console

The agent is instrumented with FriskAI to provide observability, session management, and tool call control capabilities.

## Features

### FriskAI Integration
- **Real-time Governance**: Control and monitor agent behavior in production
- **Tool Observability**: Complete visibility into all agent tool calls
- **Session Management**: Automatic session creation and tracking
- **Guard Middleware**: Real-time validation and control of tool execution
- **Data Redaction**: Configurable redaction of sensitive tool arguments and agent state
- **Callback Handlers**: Built-in callback handler for capturing LangChain events

### LangChain Components
- **Custom Agent State**: Extended state schema with `userId` and `redactMe` fields
- **Multi-LLM Support**: Supports OpenAI, Amazon Bedrock, Anthropic, or Ollama
- **Streaming Output**: Real-time streaming of agent responses
- **Tool Calling**: Multi-step reasoning with tool usage

## Prerequisites

- [Bun](https://bun.sh/) v1.0 or higher
- FriskAI API key (sign up at [frisk.ai](https://frisk.ai))
- One of the following LLM providers:
  - OpenAI API key
  - AWS credentials for Bedrock
  - Anthropic API key
  - Local Ollama installation

## Setup

1. **Install dependencies:**
   ```bash
   bun install
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your credentials:
   ```bash
   # Required: FriskAI API key
   FRISK_API_KEY="your-frisk-api-key"
   
   # Required: Choose your LLM provider
   LLM_PROVIDER="openai"  # Options: openai, bedrock, anthropic, ollama
   
   # Provider-specific configuration (choose one):
   
   # OpenAI
   OPENAI_API_KEY="your-openai-api-key"
   OPENAI_MODEL="gpt-5-nano"  # Optional
   
   # Amazon Bedrock
   AWS_REGION="us-east-1"
   AWS_ACCESS_KEY_ID="your-aws-access-key"
   AWS_SECRET_ACCESS_KEY="your-aws-secret-key"
   BEDROCK_MODEL_ID="qwen.qwen3-32b-v1:0"  # Optional
   
   # Anthropic
   ANTHROPIC_API_KEY="your-anthropic-api-key"
   ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"  # Optional
   
   # Ollama (no API key needed, runs locally)
   OLLAMA_MODEL="gpt-oss:20b"  # Optional
   ```

   Optional FriskAI configuration:
   ```bash
   FRISK_BASE_URL=""                    # Custom FriskAI endpoint
   FRISK_TOKEN_ISSUER_URL=""            # Custom token issuer
   FRISK_TELEMETRY_ENDPOINT=""          # Custom telemetry endpoint
   ```

## Usage

Run the agent with the default demo query:

```bash
bun start
```

Or run directly:

```bash
bun run src/main.ts
```

The demo executes a complex query that demonstrates all available tools:
- Adds 4.5 and 7.25
- Counts words in "how many words are in this sentence?"
- Reads the first few characters from `agent.ts`
- Looks up usernames for user IDs 42 and 43
- Logs a message containing a redacted social security number

### Example Output

```
LLM_PROVIDER not set or invalid. Defaulting to Ollama.
User input: Add 4.5 and 7.25. Count the words in 'how many words are in this sentence?'...

[Callback] LLM started
[Callback] LLM ended - add_numbers:call_123, word_count:call_456
[Middleware] Tool call ID: call_123
[Middleware] Tool call ID: call_456
[Callback] Tool started: call_123
[Callback] Tool ended: ...

LLM answer: 
The sum of 4.5 and 7.25 is 11.75. The phrase "how many words are in this sentence?" contains 7 words...
```

## Project Structure

```
.
├── src/
│   ├── main.ts          # Entry point - initializes FriskAI and runs the agent
│   ├── agent.ts         # Agent configuration with FriskAI integration
│   ├── tools.ts         # Tool definitions (5 custom tools)
│   ├── llm.ts           # LLM provider selection logic
│   ├── prompt.ts        # System prompt for the agent
│   ├── callback.ts      # Custom callback handler for debugging
│   └── middleware.ts    # Custom middleware for tool call logging
├── package.json         # Dependencies and scripts
├── .env.example         # Environment variable template
├── tsconfig.json        # TypeScript configuration
├── biome.json           # Biome linter configuration
└── README.md           # This file
```

## Key Implementation Details

### Agent Configuration (`agent.ts`)

The agent is built with FriskAI integration:

```typescript
export function buildAgent(frisk: Frisk) {
  const stateSchema = new StateSchema({
    userId: z.int(),
    redactMe: z.string().default(''),
  })
  
  const agent = createAgent({
    model: getLLM(),
    tools: frisk.wrapTools(llmTools),              // FriskAI tool wrapping
    systemPrompt,
    stateSchema,
    middleware: [frisk.guard({ stateSchema })],     // FriskAI guard middleware
  })
  
  return agent
}
```

### FriskAI Session Management (`main.ts`)

Sessions are created and used for tracking:

```typescript
const frisk = await Frisk.connect({
  apiKey: process.env.FRISK_API_KEY || '',
  redact: {
    redactToolArgs: ['path'],          // Redact file paths
    redactAgentState: ['redactMe'],    // Redact sensitive state fields
  },
})

const session = frisk.session()

const stream = await agent.stream(
  {
    messages: [new HumanMessage(userInput)],
    userId: 42,
    redactMe: 'true',
  },
  {
    callbacks: [session.callbacks],    // FriskAI callbacks
    context: session.context,          // FriskAI context
    streamMode: 'messages',
  },
)
```

### Available Tools (`tools.ts`)

Five tools are provided:

1. **add_numbers** - Adds two numbers
2. **word_count** - Counts words in text
3. **read_snippet** - Reads up to N characters from a file in `src/`
4. **lookup_username** - Returns username for a given user ID
5. **log_message** - Logs a message to console

### LLM Provider Selection (`llm.ts`)

The example supports multiple LLM providers via the `LLM_PROVIDER` environment variable:
- **OpenAI**: GPT models with streaming
- **Bedrock**: AWS-hosted models (Qwen, Claude, etc.)
- **Anthropic**: Claude models
- **Ollama**: Local open-source models (default)

## Customization

### Adding New Tools

Edit `src/tools.ts` to add new tools:

```typescript
export const myTool = tool(
  (input: { param: string }) => {
    // Tool implementation
    return `Result: ${input.param}`
  },
  {
    name: 'my_tool',
    description: 'What this tool does',
    schema: z.object({
      param: z.string().describe('Parameter description'),
    }),
  }
)

// Add to the tools array
export const llmTools = [..., myTool]
```

### Configuring Data Redaction

Modify the `redact` configuration in `main.ts`:

```typescript
const frisk = await Frisk.connect({
  apiKey: process.env.FRISK_API_KEY || '',
  redact: {
    redactToolArgs: ['password', 'apiKey', 'ssn'],     // Tool argument fields to redact
    redactAgentState: ['email', 'phoneNumber'],        // Agent state fields to redact
  },
})
```

### Changing the System Prompt

Edit `src/prompt.ts` to modify agent behavior:

```typescript
export const systemPrompt = "Your custom system prompt here..."
```

### Switching LLM Providers

Update the `LLM_PROVIDER` variable in `.env`:

```bash
# Use OpenAI
LLM_PROVIDER="openai"
OPENAI_API_KEY="sk-..."

# Use Anthropic
LLM_PROVIDER="anthropic"
ANTHROPIC_API_KEY="sk-ant-..."

# Use Ollama (local)
LLM_PROVIDER="ollama"
OLLAMA_MODEL="llama2"
```

## Development

### Linting

Run Biome linter:

```bash
bun run lint
```

### Running with Custom Input

Modify the `DEFAULT_PROMPT` in `src/main.ts` or pass a custom question to the `demoRun()` function.

## Learn More

- [FriskAI Documentation](https://docs.frisk.ai)
- [FriskAI SDK on NPM](https://www.npmjs.com/package/@friskai/frisk-js)
- [LangChain JS Documentation](https://js.langchain.com)
- [LangChain Agents Guide](https://js.langchain.com/docs/modules/agents/)

## Support

For questions or issues:
- FriskAI: Visit [docs.frisk.ai](https://docs.frisk.ai) or contact support
- LangChain: Check [js.langchain.com](https://js.langchain.com)

## License

See the repository root for license information.
