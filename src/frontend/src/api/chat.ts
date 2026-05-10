import { apiClient } from './client'
import type { ChatRequest, ChatResponse } from '@/types/api'
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
      return mod.default as ChatResponse
    }
    return mockCounseling as ChatResponse
  }
  const { data } = await apiClient.post<ChatResponse>('/chat', request)
  return data
}

export async function resetSession(sessionId: string): Promise<void> {
  mockStep = 0
  if (useMock) return
  await apiClient.post('/session/reset', { session_id: sessionId })
}
