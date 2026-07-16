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
