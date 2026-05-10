import { useEffect, useRef } from 'react'
import { useSessionStore } from '@/store/sessionStore'
import ChatMessage, { TypingIndicator } from './ChatMessage'
import ChatInput from './ChatInput'

export default function ChatArea() {
  const messages = useSessionStore((s) => s.messages)
  const isLoading = useSessionStore((s) => s.isLoading)
  const reset = useSessionStore((s) => s.reset)
  const phase = useSessionStore((s) => s.phase)

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
          <span className="text-sm font-semibold text-sage-800">AI Saju Counselor</span>
        </div>
        {phase !== 'intake' && (
          <button
            onClick={() => reset()}
            className="text-xs text-sage-400 hover:text-sage-600 transition-colors"
          >
            New reading
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

        {isLoading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <ChatInput />
    </div>
  )
}
