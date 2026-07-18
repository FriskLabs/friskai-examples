import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { createTool } from '@mastra/core/tools'
import { z } from 'zod'

export const lookupUsername = createTool({
  id: 'lookup_username',
  description: 'Function to look up a username by user ID.',
  inputSchema: z.object({
    userId: z.number().describe('The user ID to lookup'),
  }),
  execute: async (inputData) => `user_${inputData.userId}`,
})

export const addNumbers = createTool({
  id: 'add_numbers',
  description: 'Add two numbers and return the sum.',
  inputSchema: z.object({
    a: z.number().describe('First number'),
    b: z.number().describe('Second number'),
  }),
  execute: async (inputData) => inputData.a + inputData.b,
})

export const wordCount = createTool({
  id: 'word_count',
  description: 'Count the number of words in the provided text.',
  inputSchema: z.object({
    text: z.string().describe('The text to count words in'),
  }),
  execute: async (inputData) =>
    inputData.text.split(/\s+/).filter((word: string) => word.length > 0)
      .length,
})

export const readSnippet = createTool({
  id: 'read_snippet',
  description:
    'Read up to maxChars from a local file. Paths are resolved relative to src/.',
  inputSchema: z.object({
    path: z.string().describe('The file path relative to src/'),
    maxChars: z
      .number()
      .optional()
      .default(240)
      .describe('Maximum characters to read'),
  }),
  execute: async (inputData) => {
    const maxCharacters = inputData.maxChars ?? 240
    const filePath = resolve(process.cwd(), 'src', inputData.path)
    try {
      const content = readFileSync(filePath, 'utf-8')
      return (
        content.slice(0, maxCharacters) +
        (content.length > maxCharacters ? '...' : '')
      )
    } catch {
      return `Error: File not found at path ${inputData.path}`
    }
  },
})

export const logMessage = createTool({
  id: 'log_message',
  description:
    'Log a message to the console (simulating an external logging tool).',
  inputSchema: z.object({
    message: z.string().describe('The message to log'),
  }),
  execute: async (inputData) => {
    console.log(`LOG: ${inputData.message}`)
    return 'Message logged successfully.'
  },
})

export const llmTools = [
  lookupUsername,
  addNumbers,
  wordCount,
  readSnippet,
  logMessage,
]
