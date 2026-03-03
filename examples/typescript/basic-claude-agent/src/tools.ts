import { tool, type SdkMcpToolDefinition } from '@anthropic-ai/claude-agent-sdk'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { z } from 'zod'

const asToolText = (text: string) => ({
  content: [
    {
      type: 'text',
      text,
    },
  ],
})

export const lookupUsername = tool(
  'lookup_username',
  'Function to look up a username by user ID.',
  {
    userId: z.number().describe('The user ID to lookup'),
  },
  async (input: { userId: number }) => {
    return asToolText(`user_${input.userId}`)
  },
)

export const addNumbers = tool(
  'add_numbers',
  'Add two numbers and return the sum.',
  {
    a: z.number().describe('First number'),
    b: z.number().describe('Second number'),
  },
  async (input: { a: number; b: number }) => {
    return asToolText(String(input.a + input.b))
  },
)

export const wordCount = tool(
  'word_count',
  'Count the number of words in the provided text.',
  {
    text: z.string().describe('The text to count words in'),
  },
  async (input: { text: string }) => {
    const count = input.text.split(/\s+/).filter((word) => word.length > 0).length
    return asToolText(String(count))
  },
)

export const readSnippet = tool(
  'read_snippet',
  'Read up to maxChars from a local file. Paths are resolved relative to the current working directory.',
  {
    path: z.string().describe('The file path relative to src/'),
    maxChars: z
      .number()
      .optional()
      .default(240)
      .describe('Maximum characters to read'),
  },
  async (input: { path: string; maxChars?: number }) => {
    const maxCharacters = input.maxChars ?? 240
    const filePath = resolve(process.cwd(), 'src', input.path)

    try {
      const content = readFileSync(filePath, 'utf-8')
      const snippet = content.slice(0, maxCharacters)
      return asToolText(snippet + (content.length > maxCharacters ? '...' : ''))
    } catch (_error) {
      return asToolText(`Error: File not found at path ${input.path}`)
    }
  },
)

export const logMessage = tool(
  'log_message',
  'Log a message to the console (simulating an external logging tool).',
  {
    message: z.string().describe('The message to log'),
  },
  async (input: { message: string }) => {
    console.log(`LOG: ${input.message}`)
    return asToolText('Message logged successfully.')
  },
)

export const llmTools: SdkMcpToolDefinition<any>[] = [
  lookupUsername,
  addNumbers,
  wordCount,
  readSnippet,
  logMessage,
]
