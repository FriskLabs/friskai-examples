import { Frisk } from '@friskai/frisk-js/langchain'
import { HumanMessage } from '@langchain/core/messages'
import { buildAgent } from './agent.js'

const DEFAULT_PROMPT =
  'Add 4.5 and 7.25. Count the words in ' +
  "'how many words are in this sentence?', show me the first few characters of agent.ts, " +
  'tell me the username for user ID 42 and then user ID 43, ' +
  "and log the message 'Looked up user by social security number 123-45-6789'."

async function demoRun(question?: string): Promise<void> {
  const frisk = await Frisk.connect({
    apiKey: process.env.FRISK_API_KEY || '',
    redact: {
      redactToolArgs: ['path'],
      redactAgentState: ['redactMe'],
    },
  })

  const agent = buildAgent(frisk)

  const userInput = question || DEFAULT_PROMPT
  console.log('User input:', userInput)
  console.log('\nLLM answer: ')

  const session = frisk.session()

  const stream = await agent.stream(
    {
      messages: [new HumanMessage(userInput)],
      userId: 42,
      redactMe: 'true',
    },
    {
      callbacks: [session.callbacks],
      context: session.context,
      streamMode: 'messages',
    },
  )

  for await (const [message, metadata] of stream) {
    if (
      (metadata.langgraph_node === 'model' ||
        metadata.langgraph_node === 'model_request') &&
      message.content
    ) {
      const content = message.content
      if (typeof content === 'string' && content) {
        process.stdout.write(content)
      } else if (Array.isArray(content)) {
        for (const item of content) {
          if (
            typeof item === 'object' &&
            item !== null &&
            'type' in item &&
            item.type === 'text' &&
            'text' in item
          ) {
            process.stdout.write((item.text as string) || '')
          }
        }
      }
    }
  }

  console.log() // New line after streaming
  frisk.shutdown()
}

demoRun()
