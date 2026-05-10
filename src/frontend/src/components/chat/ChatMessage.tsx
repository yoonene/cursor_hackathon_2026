import { clsx } from 'clsx'
import type { ChatMessage as ChatMessageType } from '@/store/sessionStore'
import LoadingDots from '@/components/ui/LoadingDots'

type Props = {
  message: ChatMessageType
}

export default function ChatMessage({ message }: Props) {
  const isAssistant = message.role === 'assistant'

  return (
    <div className={clsx('flex gap-3', isAssistant ? 'items-start' : 'items-start flex-row-reverse')}>
      {/* Avatar */}
      {isAssistant && (
        <div className="shrink-0 w-8 h-8 rounded-full bg-sage-600 flex items-center justify-center text-sm">
          🌿
        </div>
      )}

      {/* Bubble */}
      <div
        className={clsx(
          'max-w-[78%] rounded-2xl px-4 py-3 text-sm leading-relaxed',
          isAssistant
            ? 'bg-warm-white text-sage-900 border border-sage-100 rounded-tl-sm shadow-sm'
            : 'bg-sage-600 text-white rounded-tr-sm'
        )}
      >
        {message.content}
      </div>
    </div>
  )
}

export function TypingIndicator() {
  return (
    <div className="flex gap-3 items-start">
      <div className="shrink-0 w-8 h-8 rounded-full bg-sage-600 flex items-center justify-center text-sm">
        🌿
      </div>
      <div className="bg-warm-white text-sage-900 border border-sage-100 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
        <LoadingDots />
      </div>
    </div>
  )
}
