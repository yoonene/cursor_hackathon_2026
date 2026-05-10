import { apiClient } from './client'
import type { StartReadingRequest, InitialReadingResponse } from '@/types/api'
import mockInitial from '@/mocks/01_initial_reading_response.json'

const useMock = import.meta.env.VITE_USE_MOCK === 'true'

export async function startReading(request: StartReadingRequest): Promise<InitialReadingResponse> {
  if (useMock) {
    await new Promise((r) => setTimeout(r, 1200))
    return mockInitial as InitialReadingResponse
  }
  const { data } = await apiClient.post<InitialReadingResponse>('/reading/start', request)
  return data
}

export type ReadingSSEHandlers = {
  onDelta?: (text: string) => void
  onComplete?: (payload: InitialReadingResponse) => void
  onError?: (error: Error) => void
}

export async function startReadingStream(
  request: StartReadingRequest,
  handlers: ReadingSSEHandlers,
): Promise<void> {
  if (useMock) {
    const data = mockInitial as InitialReadingResponse
    await new Promise((r) => setTimeout(r, 300))
    const msg = data.assistant_message
    for (let i = 0; i < msg.length; i += 8) {
      handlers.onDelta?.(msg.slice(i, i + 8))
      await new Promise((r) => setTimeout(r, 18))
    }
    handlers.onComplete?.(data)
    return
  }

  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
  let res: Response
  try {
    res = await fetch(`${baseUrl}/reading/start-stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    })
  } catch (e) {
    handlers.onError?.(e instanceof Error ? e : new Error(String(e)))
    return
  }

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
          try {
            const payload = JSON.parse(line.slice(6))
            if (eventName === 'delta') {
              handlers.onDelta?.(payload.text as string)
            } else if (eventName === 'complete') {
              handlers.onComplete?.(payload as InitialReadingResponse)
            }
          } catch {
            // JSON 파싱 실패 시 무시
          }
        }
      }
    }
  } catch (e) {
    handlers.onError?.(e instanceof Error ? e : new Error(String(e)))
  }
}
