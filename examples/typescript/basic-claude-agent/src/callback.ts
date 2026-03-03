import { BaseCallbackHandler } from '@langchain/core/callbacks/base'
import type { Serialized } from '@langchain/core/load/serializable'
import { AIMessage } from '@langchain/core/messages'
import type { Generation, LLMResult } from '@langchain/core/outputs'

export class CallbackHandler extends BaseCallbackHandler {
  name = 'CallbackHandler'

  async handleToolStart(
    _tool: Serialized,
    _input: string,
    _runId: string,
    _parentRunId?: string,
    _tags?: string[],
    metadata?: Record<string, unknown>,
    name?: string,
  ): Promise<void> {
    console.log(`[Callback] Tool started: ${metadata?.tool_call_id || name}\n`)
  }

  async handleToolEnd(
    _output: string,
    runId: string,
    _parentRunId?: string,
    _tags?: string[],
  ): Promise<void> {
    console.log(`[Callback] Tool ended: ${runId}\n`)
  }

  async handleLLMStart(
    _llm: Serialized,
    _prompts: string[],
    _runId: string,
    _parentRunId?: string,
    _extraParams?: Record<string, unknown>,
    _tags?: string[],
    _metadata?: Record<string, unknown>,
  ): Promise<void> {
    console.log('[Callback] LLM started\n')
  }

  async handleLLMEnd(
    output: LLMResult,
    _runId: string,
    _parentRunId?: string,
    _tags?: string[],
  ): Promise<void> {
    const toolCalls = printToolCallsFromLLMResult(output)
    console.log(`[Callback] LLM ended - ${toolCalls.join(', ')}\n`)
  }
}

function printToolCallsFromLLMResult(llmResult: LLMResult): string[] {
  const result: string[] = []

  for (const generation of llmResult.generations) {
    for (const gen of generation) {
      const generationWithMessage = gen as Generation & { message?: AIMessage }
      if (
        generationWithMessage.message &&
        generationWithMessage.message instanceof AIMessage
      ) {
        const message = generationWithMessage.message
        if (message.tool_calls) {
          for (const toolCall of message.tool_calls) {
            result.push(`${toolCall.name}:${toolCall.id}`)
          }
        }
      }
    }
  }

  return result
}
