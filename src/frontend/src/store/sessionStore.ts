import { create } from 'zustand'
import type {
  SajuReport,
  CounselingBoard,
  RecommendedTab,
  CurrentStage,
} from '@/types/api'

export type Phase = 'intake' | 'reading' | 'counseling'

export type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
}

type SessionState = {
  sessionId: string
  phase: Phase
  currentStage: CurrentStage | null
  messages: ChatMessage[]
  sajuReport: SajuReport | null
  counselingBoard: CounselingBoard | null
  activeTab: RecommendedTab
  isLoading: boolean
  error: string | null
}

type SessionActions = {
  setPhase: (phase: Phase) => void
  setActiveTab: (tab: RecommendedTab) => void
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void
  setReadingResult: (payload: {
    sajuReport: SajuReport
    counselingBoard: CounselingBoard
    assistantMessage: string
    currentStage: CurrentStage
    recommendedTab: RecommendedTab
  }) => void
  setChatResult: (payload: {
    sajuReport: SajuReport
    counselingBoard: CounselingBoard
    assistantMessage: string
    currentStage: CurrentStage
    recommendedTab: RecommendedTab
  }) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  reset: () => void
}

const initialState: SessionState = {
  sessionId: `session-${Date.now()}`,
  phase: 'intake',
  currentStage: null,
  messages: [],
  sajuReport: null,
  counselingBoard: null,
  activeTab: 'saju_report',
  isLoading: false,
  error: null,
}

export const useSessionStore = create<SessionState & SessionActions>((set) => ({
  ...initialState,

  setPhase: (phase) => set({ phase }),

  setActiveTab: (tab) => set({ activeTab: tab }),

  addMessage: (message) =>
    set((state) => ({
      messages: [
        ...state.messages,
        { ...message, id: `msg-${Date.now()}-${Math.random()}`, timestamp: Date.now() },
      ],
    })),

  setReadingResult: ({ sajuReport, counselingBoard, assistantMessage, currentStage, recommendedTab }) =>
    set((state) => ({
      sajuReport,
      counselingBoard,
      currentStage,
      activeTab: recommendedTab,
      phase: 'reading',
      messages: [
        ...state.messages,
        {
          id: `msg-${Date.now()}`,
          role: 'assistant',
          content: assistantMessage,
          timestamp: Date.now(),
        },
      ],
    })),

  setChatResult: ({ sajuReport, counselingBoard, assistantMessage, currentStage, recommendedTab }) =>
    set((state) => ({
      sajuReport,
      counselingBoard,
      currentStage,
      activeTab: recommendedTab,
      phase: currentStage === 'open_counseling' ? 'counseling' : state.phase,
      messages: [
        ...state.messages,
        {
          id: `msg-${Date.now()}`,
          role: 'assistant',
          content: assistantMessage,
          timestamp: Date.now(),
        },
      ],
    })),

  setLoading: (loading) => set({ isLoading: loading }),

  setError: (error) => set({ error }),

  reset: () =>
    set({
      ...initialState,
      sessionId: `session-${Date.now()}`,
    }),
}))
