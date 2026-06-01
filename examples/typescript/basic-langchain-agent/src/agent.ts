import type { Frisk } from '@friskai/frisk-js/langchain'
import type { DynamicStructuredTool } from '@langchain/core/tools'
import {
  MemorySaver,
  StateSchema,
    MessagesValue
} from '@langchain/langgraph'
import { createAgent } from 'langchain'
import type { ZodObject } from 'zod'
import { z } from 'zod'
import { getLLM } from './llm.js'
import { systemPrompt } from './prompt.js'
import { llmTools } from './tools.js'

export const agentStateSchema = new StateSchema({
  messages: MessagesValue,
  userId: z.int(),
  redactMe: z.string().default(''),
})

export function buildAgent(frisk: Frisk) {
  const agent = createAgent({
    model: getLLM(),
    tools: frisk.wrapTools(
      llmTools as Iterable<DynamicStructuredTool<ZodObject>>,
    ),
    systemPrompt,
    stateSchema: agentStateSchema,
    middleware: [
      frisk.guard({ stateSchema: agentStateSchema })
    ],
    checkpointer: new MemorySaver(),
  })

  return agent
}
