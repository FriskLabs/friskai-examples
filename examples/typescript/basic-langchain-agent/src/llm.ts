import { ChatAnthropic } from '@langchain/anthropic'
import { ChatBedrockConverse } from '@langchain/aws'
import { ChatOllama } from '@langchain/ollama'
import { ChatOpenAI } from '@langchain/openai'

export function getLLM() {
  const provider = (process.env.LLM_PROVIDER || '').toLowerCase()

  if (provider === 'openai') {
    console.log('Using OpenAI LLM (LLM_PROVIDER=openai).')
    return new ChatOpenAI({
      model: process.env.OPENAI_MODEL || 'gpt-5-nano',
      temperature: 0.0,
      streaming: true,
    })
  } else if (provider === 'bedrock') {
    console.log('Using Amazon Bedrock LLM (LLM_PROVIDER=bedrock).')
    return new ChatBedrockConverse({
      model: process.env.BEDROCK_MODEL_ID || 'qwen.qwen3-32b-v1:0',
      temperature: 0.0,
      region: process.env.AWS_REGION || 'us-east-1',
      streaming: true,
    })
  } else if (provider === 'anthropic') {
    console.log('Using Anthropic LLM (LLM_PROVIDER=anthropic).')
    return new ChatAnthropic({
      model: process.env.ANTHROPIC_MODEL || 'claude-3-5-sonnet-20241022',
      temperature: 0.0,
      streaming: true,
    })
  } else {
    console.log('LLM_PROVIDER not set or invalid. Defaulting to Ollama.')
    return new ChatOllama({
      model: process.env.OLLAMA_MODEL || 'gpt-oss:20b',
      temperature: 0.0,
    })
  }
}
