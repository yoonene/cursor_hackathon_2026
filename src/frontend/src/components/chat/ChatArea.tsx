import { useEffect, useRef } from 'react'
import { useSessionStore } from '@/store/sessionStore'
import ChatMessage, { TypingIndicator } from './ChatMessage'
import ChatInput from './ChatInput'
import PartnerIntakeModal from './PartnerIntakeModal'

export default function ChatArea() {
  const messages = useSessionStore((s) => s.messages)
  const isLoading = useSessionStore((s) => s.isLoading)
  const isStreaming = useSessionStore((s) => s.isStreaming)
  const reset = useSessionStore((s) => s.reset)
  const phase = useSessionStore((s) => s.phase)
  const partnerIntakeRequested = useSessionStore((s) => s.partnerIntakeRequested)

  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  return (
    <div className="flex flex-col h-full bg-sage-50">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-sage-200 bg-warm-white">
        <div className="flex items-center gap-2">
          <span className="text-lg">🌿</span>
          <span className="text-sm font-semibold text-sage-800">Fate.me</span>
        </div>
        {phase !== 'intake' && (
          <button
            onClick={() => reset()}
            className="flex items-center gap-1.5 text-xs text-sage-600 border border-sage-400 hover:border-sage-600 hover:bg-sage-100 rounded-md px-3 py-1 transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
              <polyline points="9 22 9 12 15 12 15 22" />
            </svg>
            New session
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-5 py-6 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center gap-2">
            <span className="text-3xl">🌱</span>
            <p className="text-sage-400 text-sm">Your reading will appear here.</p>
          </div>
        )}

        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}

        {isLoading && !isStreaming && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <ChatInput />

      {/* Partner intake popup */}
      {partnerIntakeRequested && <PartnerIntakeModal />}
    </div>
  )
}
