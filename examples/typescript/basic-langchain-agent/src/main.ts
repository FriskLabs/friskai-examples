import { Frisk } from '@friskai/frisk-js/langchain'
import { HumanMessage } from '@langchain/core/messages'
import { Command } from '@langchain/langgraph'
import { buildAgent } from './agent.js'

const DEFAULT_PROMPT =
  'Add 4.5 and 7.25. Count the words in ' +
  "'how many words are in this sentence?', show me the first few characters of agent.ts, " +
  'tell me the username for user ID 42 and then user ID 43, ' +
  "and log the message 'Looked up user by social security number 123-45-6789'."

const DEFAULT_THREAD_ID = 'in_memory_thread'
const INTERRUPT_POLLING_INTERVAL_MS = 5_000

type ToolCallResumeAction = 'retry' | 'cancel'
type ResumeDecisions = Record<string, ToolCallResumeAction>

class DemoRunner {
  private readonly agent: ReturnType<typeof buildAgent>

  private constructor(private readonly frisk: Frisk) {
    this.agent = buildAgent(frisk)
  }

  static async create(): Promise<DemoRunner> {
    const frisk = await Frisk.connect({
      apiKey: process.env.FRISK_API_KEY || '',
      redact: {
        redactToolArgs: ['path'],
        redactAgentState: ['redactMe'],
      },
    })

    return new DemoRunner(frisk)
  }

  async run({
    threadId,
    question,
  }: {
    threadId: string
    question?: string
  }): Promise<void> {
    const userInput = question || DEFAULT_PROMPT
    console.log('User input:', userInput)
    console.log('\nLLM answer: ')

    let input:
      | {
          messages: HumanMessage[]
          userId: number
          redactMe: string
        }
      | Command = {
      messages: [new HumanMessage(userInput)],
      userId: 42,
      redactMe: 'true',
    }

    while (true) {
      const session = this.frisk.session()
        // console.log({ input }) // todo!
      const stream = await this.agent.stream(input, {
        callbacks: [session.callbacks],
        context: session.context,
        streamMode: ['messages', 'updates'],
        subgraphs: true,
        configurable: {
          thread_id: threadId,
        },
      })

      let nextResume: ResumeDecisions | null = null

      for await (const event of stream as AsyncIterable<unknown>) {
        const parsedEvent = parseStreamEvent(event)
        if (!parsedEvent) {
          continue
        }

        if (parsedEvent.streamMode === 'updates') {
          const interruptData = getInterruptData(parsedEvent.chunk)
          if (interruptData?.__frisk) {
            nextResume = makeRetryDecisionMap(
              interruptData.escalated_tool_calls,
            )
          }
          continue
        }

        streamMessageChunk(parsedEvent.chunk)
      }

      console.log()

      if (!nextResume || Object.keys(nextResume).length === 0) {
        return
      }

      console.log(
        `Some tool calls were escalated. Trying again in ${INTERRUPT_POLLING_INTERVAL_MS / 1000} seconds...`,
      )
      await sleep(INTERRUPT_POLLING_INTERVAL_MS)
      console.log('Retrying escalated tool calls...')
      input = new Command({ resume: nextResume })
    }
  }

  shutdown(): void {
    this.frisk.shutdown()
  }
}

async function demoRun(question?: string): Promise<void> {
  const runner = await DemoRunner.create()

  try {
    await runner.run({
      question,
      threadId: DEFAULT_THREAD_ID,
    })
  } finally {
    runner.shutdown()
  }
}

function parseStreamEvent(
  event: unknown,
): { streamMode: string; chunk: unknown } | null {
  if (!Array.isArray(event)) {
    return null
  }

  if (event.length >= 3 && typeof event[1] === 'string') {
    return {
      streamMode: event[1],
      chunk: event[2],
    }
  }

  if (event.length >= 2 && typeof event[0] === 'string') {
    return {
      streamMode: event[0],
      chunk: event[1],
    }
  }

  return null
}

function streamMessageChunk(chunk: unknown): void {
  if (!Array.isArray(chunk) || chunk.length === 0) {
    return
  }

  const [message] = chunk
  if (!isRecord(message)) {
    return
  }

  const messageType =
    typeof message.type === 'string' ? message.type.toLowerCase() : ''
  if (messageType !== 'aimessagechunk' && messageType !== 'ai') {
    return
  }

  if (typeof message.text === 'function') {
    const text = message.text()
    if (typeof text === 'string' && text) {
      process.stdout.write(text)
    }
    return
  }

  const content = message.content
  if (typeof content === 'string' && content) {
    process.stdout.write(content)
    return
  }

  if (!Array.isArray(content)) {
    return
  }

  for (const item of content) {
    if (!isRecord(item) || item.type !== 'text') {
      continue
    }

    if (typeof item.text === 'string' && item.text) {
      process.stdout.write(item.text)
    }
  }
}

function getInterruptData(chunk: unknown): Record<string, unknown> | null {
  if (!isRecord(chunk) || !('__interrupt__' in chunk)) {
    return null
  }

  const interruptList = chunk.__interrupt__
  if (!Array.isArray(interruptList) || interruptList.length === 0) {
    return null
  }

  const [firstInterrupt] = interruptList
  if (!isRecord(firstInterrupt) || !('value' in firstInterrupt)) {
    return null
  }

  return asRecord(firstInterrupt.value)
}

function makeRetryDecisionMap(
  escalatedToolCalls: unknown,
): ResumeDecisions | null {
  const toolCalls = asRecord(escalatedToolCalls)
  const toolCallIds = Object.keys(toolCalls)

  if (toolCallIds.length === 0) {
    return null
  }

  return Object.fromEntries(
    toolCallIds.map((toolCallId) => [toolCallId, 'retry']),
  ) as ResumeDecisions
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function asRecord(value: unknown): Record<string, unknown> {
  return isRecord(value) ? value : {}
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

const question = process.argv.length > 2 ? process.argv[2] : undefined

await demoRun(question)
