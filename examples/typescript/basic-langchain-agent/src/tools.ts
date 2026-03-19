import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { tool } from '@langchain/core/tools'
import { z } from 'zod'

export const lookupUsername = tool(
  (input: { userId: number }) => {
    return `user_${input.userId}`
  },
  {
    name: 'lookup_username',
    description: 'Function to look up a username by user ID.',
    schema: z.object({
      userId: z.number().describe('The user ID to lookup'),
    }),
  },
)

export const addNumbers = tool(
  (input: { a: number; b: number }) => {
    return input.a + input.b
  },
  {
    name: 'add_numbers',
    description: 'Add two numbers and return the sum.',
    schema: z.object({
      a: z.number().describe('First number'),
      b: z.number().describe('Second number'),
    }),
  },
)

export const wordCount = tool(
  (input: { text: string }) => {
    return input.text.split(/\s+/).filter((word) => word.length > 0).length
  },
  {
    name: 'word_count',
    description: 'Count the number of words in the provided text.',
    schema: z.object({
      text: z.string().describe('The text to count words in'),
    }),
  },
)

export const readSnippet = tool(
  (input: { path: string; maxChars?: number }) => {
    const maxCharacters = input.maxChars ?? 240
    const filePath = resolve(process.cwd(), 'src', input.path)

    try {
      const content = readFileSync(filePath, 'utf-8')
      const snippet = content.slice(0, maxCharacters)
      return snippet + (content.length > maxCharacters ? '...' : '')
    } catch (_error) {
      //throw new Error(`File not found: ${filePath}`);
      return `Error: File not found at path ${input.path}`
    }
  },
  {
    name: 'read_snippet',
    description:
      'Read up to maxChars from a local file. Paths are resolved relative to the current working directory.',
    schema: z.object({
      path: z.string().describe('The file path relative to src/'),
      maxChars: z
        .number()
        .optional()
        .default(240)
        .describe('Maximum characters to read'),
    }),
  },
)

export const logMessage = tool(
  (input: { message: string }) => {
    console.log(`LOG: ${input.message}`)
    return 'Message logged successfully.'
  },
  {
    name: 'log_message',
    description:
      'Log a message to the console (simulating an external logging tool).',
    schema: z.object({
      message: z.string().describe('The message to log'),
    }),
  },
)

export const llmTools = [
  lookupUsername,
  addNumbers,
  wordCount,
  readSnippet,
  logMessage,
]
