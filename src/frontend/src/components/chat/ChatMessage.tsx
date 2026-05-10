import { clsx } from 'clsx'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
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
        {isAssistant ? (
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
              strong: ({ children }) => <strong className="font-semibold text-sage-800">{children}</strong>,
              em: ({ children }) => <em className="italic">{children}</em>,
              ul: ({ children }) => <ul className="list-disc list-inside space-y-1 mb-2">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 mb-2">{children}</ol>,
              li: ({ children }) => <li className="leading-relaxed">{children}</li>,
              h1: ({ children }) => <h1 className="text-base font-bold text-sage-800 mb-1">{children}</h1>,
              h2: ({ children }) => <h2 className="text-sm font-bold text-sage-800 mb-1">{children}</h2>,
              h3: ({ children }) => <h3 className="text-sm font-semibold text-sage-700 mb-1">{children}</h3>,
              code: ({ children }) => (
                <code className="bg-sage-100 text-sage-800 rounded px-1 py-0.5 text-xs font-mono">{children}</code>
              ),
              blockquote: ({ children }) => (
                <blockquote className="border-l-2 border-sage-300 pl-3 text-sage-600 italic mb-2">{children}</blockquote>
              ),
              hr: () => <hr className="border-sage-200 my-2" />,
            }}
          >
            {message.content}
          </ReactMarkdown>
        ) : (
          message.content
        )}
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
