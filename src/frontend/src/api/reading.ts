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
