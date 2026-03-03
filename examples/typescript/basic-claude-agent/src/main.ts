import { Frisk } from '@friskai/frisk-js/claude'
import { HumanMessage } from '@langchain/core/messages'
import { buildAgent } from './agent.js'
import { createSdkMcpServer, query } from '@anthropic-ai/claude-agent-sdk'
import {llmTools} from "./tools.ts";

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

  const prompt = question || DEFAULT_PROMPT
  console.log('User input:', prompt)
  console.log('\nLLM answer: ')

  const session = frisk.session({ dontRedactMe: 'foo', redactMe: 'bar' })

  const stream = query({
    prompt,
    options: {
        model: 'claude-haiku-4-5',
      mcpServers: {
        'basic-claude-tools': createSdkMcpServer({
          name: 'basic-claude-tools',
          version: '0.0.1',
          tools: frisk.wrapTools(llmTools),
        })
      },
      allowedTools: [
          'mcp__basic-claude-tools__*'
      ],
      includePartialMessages: true,
      hooks: session.hooks()
    }
  })

  for await (const messageChunk of stream) {
    if (messageChunk.type === 'stream_event') {
                const event = messageChunk.event
                if (event.type === 'content_block_delta') {
                  if (event.delta.text) {
                    process.stdout.write(event.delta.text)
                  }
                }
              }
  }

  console.log() // New line after streaming
  frisk.shutdown()
}

demoRun()
