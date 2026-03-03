import {
  createMiddleware,
  type ToolCallHandler,
  type ToolCallRequest,
} from 'langchain'

export const toolCallMiddleware = createMiddleware({
  name: 'ToolCallMiddleware',
  wrapToolCall: async (
    request: ToolCallRequest<any, any>,
    handler: ToolCallHandler,
  ) => {
    console.log(`[Middleware] Tool call ID: ${request.toolCall.id}\n`)
    const result = await handler(request)
    return result
  },
})
