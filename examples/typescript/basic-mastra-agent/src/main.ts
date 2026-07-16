import { Frisk } from '@friskai/frisk-js/mastra'
import type { Memory } from '@mastra/memory'
import { buildMastra } from './agent.js'

// A fixed thread id plus an on-disk LibSQL store means every run continues the
// SAME conversation, even across separate processes.
const THREAD_ID = 'mastra_chati2'
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
  // Equivalent to the documented `Frisk.connect(options)` factory, which is
  // exactly `new Frisk(options)` + `await connect()`. The two-step form is used
  // because the static factory's generic `this` signature does not typecheck
  // against the Mastra `Frisk` subclass (an SDK issue, not a usage error).
  const frisk = new Frisk({
    apiKey: process.env.FRISK_API_KEY || '',
    redact: {
      redactToolArgs: ['path'],
      redactAgentState: ['redactMe'],
    },
  })
  await frisk.connect()

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
