import { useState } from 'react'
import { useSessionStore } from '@/store/sessionStore'

const SUGGESTED_PROMPTS = [
  "I've been seeing someone lately.",
  "I'm thinking of confessing soon.",
  "How does my career flow look this week?",
  "It feels like money keeps slipping away.",
]

export default function ChatInput() {
  const submitMessage = useSessionStore((s) => s.submitMessage)
  const isLoading = useSessionStore((s) => s.isLoading)
  const phase = useSessionStore((s) => s.phase)

  const [text, setText] = useState('')

  const send = () => {
    const trimmed = text.trim()
    if (!trimmed || isLoading) return
    submitMessage(trimmed)
    setText('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  if (phase === 'intake') return null

  return (
    <div className="border-t border-sage-200 bg-warm-white px-4 pt-3 pb-4 space-y-3">
      {/* Suggested prompts — shown whenever not loading */}
      {!isLoading && (
        <div className="flex flex-wrap gap-2">
          {SUGGESTED_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              onClick={() => {
                setText(prompt)
              }}
              className="rounded-full border border-sage-200 bg-sage-50 px-3 py-1.5 text-xs text-sage-600 hover:bg-sage-100 hover:border-sage-300 transition-colors"
            >
              {prompt}
            </button>
          ))}
        </div>
      )}

      {/* Input row */}
      <div className="flex gap-2 items-end">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="What has been on your mind lately?"
          rows={1}
          disabled={isLoading}
          className="flex-1 resize-none rounded-xl border border-sage-200 bg-sage-50 px-4 py-2.5 text-sm text-sage-900 placeholder:text-sage-300 focus:outline-none focus:ring-2 focus:ring-sage-400 focus:border-transparent disabled:opacity-50 transition min-h-[42px] max-h-32"
          style={{ fieldSizing: 'content' } as React.CSSProperties}
        />
        <button
          onClick={send}
          disabled={!text.trim() || isLoading}
          className="shrink-0 w-10 h-10 rounded-xl bg-sage-600 text-white flex items-center justify-center hover:bg-sage-700 active:bg-sage-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          aria-label="Send"
        >
          <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none">
            <path d="M2 8l12-6-5 6 5 6-12-6z" fill="currentColor" />
          </svg>
        </button>
      </div>
    </div>
  )
}
