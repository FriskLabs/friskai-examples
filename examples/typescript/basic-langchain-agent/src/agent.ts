import type { Frisk } from '@friskai/frisk-js/langchain'
import type { DynamicStructuredTool } from '@langchain/core/tools'
import { StateSchema } from '@langchain/langgraph'
import { createAgent } from 'langchain'
import type { ZodObject } from 'zod'
import { z } from 'zod'
import { getLLM } from './llm.js'
import { systemPrompt } from './prompt.js'
import { llmTools } from './tools.js'

export interface CustomContext {
  friskSessionId?: string
}

export function buildAgent(frisk: Frisk) {
  const stateSchema = new StateSchema({
    userId: z.int(),
    redactMe: z.string().default(''),
  })
  const agent = createAgent({
    model: getLLM(),
    tools: frisk.wrapTools(
      llmTools as Iterable<DynamicStructuredTool<ZodObject>>,
    ),
    systemPrompt,
    stateSchema,
    middleware: [frisk.guard({ stateSchema })],
  })

  return agent
}
