import { create } from 'zustand'
import type {
  SajuReport,
  CounselingBoard,
  RecommendedTab,
  CurrentStage,
  StartReadingRequest,
  PartnerCompatibilityPayload,
} from '@/types/api'
import { startReadingStream } from '@/api/reading'
import { sendChat, resetSession } from '@/api/chat'

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
  isStreaming: boolean
  error: string | null
  partnerIntakeRequested: boolean
}

type SessionActions = {
  submitIntake: (request: Omit<StartReadingRequest, 'session_id'>) => Promise<void>
  submitMessage: (text: string) => Promise<void>
  submitPartner: (partner: PartnerCompatibilityPayload) => Promise<void>
  setActiveTab: (tab: RecommendedTab) => void
  closePartnerIntake: () => void
  reset: () => Promise<void>
}

const makeId = () => `msg-${Date.now()}-${Math.random().toString(36).slice(2)}`

const initialState: SessionState = {
  sessionId: `session-${Date.now()}`,
  phase: 'intake',
  currentStage: null,
  messages: [],
  sajuReport: null,
  counselingBoard: null,
  activeTab: 'saju_report',
  isLoading: false,
  isStreaming: false,
  error: null,
  partnerIntakeRequested: false,
}

export const useSessionStore = create<SessionState & SessionActions>((set, get) => ({
  ...initialState,

  setActiveTab: (tab) => set({ activeTab: tab }),

  closePartnerIntake: () => set({ partnerIntakeRequested: false }),

  submitIntake: async (request) => {
    set({ isLoading: true, isStreaming: false, error: null })
    const sessionId = get().sessionId
    const msgId = makeId()

    await startReadingStream({ ...request, session_id: sessionId }, {
      onDelta: (text) => {
        set((state) => {
          const exists = state.messages.some((m) => m.id === msgId)
          if (!exists) {
            return {
              phase: 'reading' as Phase,
              isStreaming: true,
              messages: [
                ...state.messages,
                { id: msgId, role: 'assistant' as const, content: text, timestamp: Date.now() },
              ],
            }
          }
          return {
            messages: state.messages.map((m) =>
              m.id === msgId ? { ...m, content: m.content + text } : m,
            ),
          }
        })
      },
      onComplete: (res) => {
        set((state) => ({
          currentStage: res.current_stage,
          activeTab: res.recommended_tab,
          sajuReport: res.saju_report,
          counselingBoard: res.counseling_board,
          isLoading: false,
          isStreaming: false,
          messages: state.messages.map((m) =>
            m.id === msgId ? { ...m, content: res.assistant_message } : m,
          ),
        }))
      },
      onError: (error) => {
        console.error('Initial reading stream error:', error)
        set({ isLoading: false, isStreaming: false, error: 'Something went wrong. Please try again.' })
      },
    })
  },

  submitMessage: async (text) => {
    const userMsg: ChatMessage = { id: makeId(), role: 'user', content: text, timestamp: Date.now() }
    set((state) => ({
      isLoading: true,
      error: null,
      partnerIntakeRequested: false,
      messages: [...state.messages, userMsg],
    }))
    try {
      const res = await sendChat({ session_id: get().sessionId, message: text })
      set((state) => ({
        currentStage: res.current_stage,
        activeTab: res.recommended_tab,
        sajuReport: res.saju_report,
        counselingBoard: res.counseling_board,
        phase: 'counseling',
        isLoading: false,
        partnerIntakeRequested: res.partner_intake_requested ?? false,
        messages: [
          ...state.messages,
          {
            id: makeId(),
            role: 'assistant',
            content: res.assistant_message,
            timestamp: Date.now(),
          },
        ],
      }))
    } catch (e) {
      set({ isLoading: false, error: 'Something went wrong. Please try again.' })
      console.error(e)
    }
  },

  submitPartner: async (partner) => {
    set({ isLoading: true, error: null, partnerIntakeRequested: false })
    try {
      const res = await sendChat({ session_id: get().sessionId, message: '', partner })
      set((state) => ({
        currentStage: res.current_stage,
        activeTab: res.recommended_tab,
        sajuReport: res.saju_report,
        counselingBoard: res.counseling_board,
        phase: 'counseling',
        isLoading: false,
        partnerIntakeRequested: res.partner_intake_requested ?? false,
        messages: [
          ...state.messages,
          {
            id: makeId(),
            role: 'assistant',
            content: res.assistant_message,
            timestamp: Date.now(),
          },
        ],
      }))
    } catch (e) {
      set({ isLoading: false, error: 'Something went wrong. Please try again.' })
      console.error(e)
    }
  },

  reset: async () => {
    const { sessionId } = get()
    await resetSession(sessionId).catch(() => {})
    set({ ...initialState, sessionId: `session-${Date.now()}` })
  },
}))
