import type { Frisk } from '@friskai/frisk-js/mastra'
import { Mastra } from '@mastra/core'
import type { Agent } from '@mastra/core/agent'
import { Agent as MastraAgent } from '@mastra/core/agent'
import type { ObservabilityExporter } from '@mastra/core/observability'
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
          serviceName: 'basic-mastra-agent',
          exporters: [frisk.exporter() as unknown as ObservabilityExporter],
        },
      },
    }),
  })

  return { agent: mastra.getAgent(AGENT_NAME), memory }
}
