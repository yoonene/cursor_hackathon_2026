import { apiClient } from './client'
import type { ChatRequest, ChatResponse, PreludePayload } from '@/types/api'
import mockCounseling from '@/mocks/02_counseling_start_general_reading.json'

const useMock = import.meta.env.VITE_USE_MOCK === 'true'

let mockStep = 0
const mockSequence = [
  () => import('@/mocks/02_counseling_start_general_reading.json'),
  () => import('@/mocks/03_compatibility_pending.json'),
  () => import('@/mocks/04_compatibility_result.json'),
  () => import('@/mocks/05_timing_recommendation_love.json'),
  () => import('@/mocks/06_fortune_flow_career_week.json'),
  () => import('@/mocks/07_timing_recommendation_career.json'),
]

export async function sendChat(request: ChatRequest): Promise<ChatResponse> {
  if (useMock) {
    await new Promise((r) => setTimeout(r, 900))
    if (mockStep < mockSequence.length) {
      const mod = await mockSequence[mockStep++]()
      const data = mod.default as unknown as Partial<ChatResponse>
      return { partner_intake_requested: false, ...data } as ChatResponse
    }
    return { partner_intake_requested: false, ...(mockCounseling as unknown as Partial<ChatResponse>) } as ChatResponse
  }
  const { data } = await apiClient.post<ChatResponse>('/chat', request)
  return data
}

export type SSEHandlers = {
  onPrelude?: (payload: PreludePayload) => void
  onDelta?: (text: string) => void
  onComplete?: (payload: ChatResponse) => void
  onError?: (error: Error) => void
}

export async function sendChatStream(
  request: ChatRequest,
  handlers: SSEHandlers,
): Promise<void> {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
  const res = await fetch(`${baseUrl}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  if (!res.ok || !res.body) {
    handlers.onError?.(new Error(`SSE request failed: ${res.status}`))
    return
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''

      let eventName = ''
      for (const line of lines) {
        if (line.startsWith('event: ')) {
          eventName = line.slice(7).trim()
        } else if (line.startsWith('data: ')) {
          const payload = JSON.parse(line.slice(6))
          if (eventName === 'prelude') {
            handlers.onPrelude?.(payload as PreludePayload)
          } else if (eventName === 'delta') {
            handlers.onDelta?.(payload.text as string)
          } else if (eventName === 'complete') {
            handlers.onComplete?.(payload as ChatResponse)
          }
        }
      }
    }
  } catch (e) {
    handlers.onError?.(e instanceof Error ? e : new Error(String(e)))
  }
}

export async function resetSession(sessionId: string): Promise<void> {
  mockStep = 0
  if (useMock) return
  await apiClient.post('/session/reset', { session_id: sessionId })
}
