import type { Phase } from '@/store/sessionStore'
import IntakeForm from '@/components/intake/IntakeForm'
import ChatArea from '@/components/chat/ChatArea'
import RightPanel from '@/components/right-panel/RightPanel'

type Props = {
  phase: Phase
}

export default function MainPage({ phase }: Props) {
  if (phase === 'intake') {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <IntakeForm />
      </div>
    )
  }

  return (
    <div className="h-screen flex overflow-hidden">
      <div className="flex-1 min-w-0 flex flex-col border-r border-sage-200">
        <ChatArea />
      </div>
      <div className="w-[480px] shrink-0 flex flex-col bg-mist">
        <RightPanel />
      </div>
    </div>
  )
}
