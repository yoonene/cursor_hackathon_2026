import { useSessionStore } from '@/store/sessionStore'
import type { RecommendedTab } from '@/types/api'
import SajuReportTab from './saju-report/SajuReportTab'
import CounselingBoard from './counseling-board/CounselingBoard'

const TABS: { id: RecommendedTab; label: string }[] = [
  { id: 'saju_report', label: 'Full Saju Report' },
  { id: 'counseling_board', label: 'Counseling Board' },
]

export default function RightPanel() {
  const activeTab = useSessionStore((s) => s.activeTab)
  const setActiveTab = useSessionStore((s) => s.setActiveTab)
  const sajuReport = useSessionStore((s) => s.sajuReport)
  const counselingBoard = useSessionStore((s) => s.counselingBoard)
  const phase = useSessionStore((s) => s.phase)
  const isLoading = useSessionStore((s) => s.isLoading)

  if (phase === 'intake') {
    return (
      <div className="flex flex-col h-full items-center justify-center px-8 text-center">
        <span className="text-4xl mb-4">✦</span>
        <p className="text-sage-400 text-sm leading-relaxed">
          Your saju report and counseling board will appear here after the reading begins.
        </p>
      </div>
    )
  }

  const isInitialLoading = isLoading && sajuReport === null && counselingBoard === null

  return (
    <div className="flex flex-col h-full relative">
      {/* Tab bar */}
      <div className="flex border-b border-sage-200 bg-warm-white shrink-0">
        {TABS.map((tab) => {
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 py-3.5 text-xs font-semibold tracking-wide transition-colors ${
                isActive
                  ? 'text-sage-800 border-b-2 border-sage-600 bg-warm-white'
                  : 'text-sage-400 hover:text-sage-600 border-b-2 border-transparent'
              }`}
            >
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto relative">
        {isInitialLoading ? (
          <BoardLoadingState />
        ) : (
          <>
            {activeTab === 'saju_report' && (
              sajuReport
                ? <SajuReportTab report={sajuReport} />
                : <EmptyState message="Your full saju report will appear here." />
            )}
            {activeTab === 'counseling_board' && (
              counselingBoard
                ? <CounselingBoard board={counselingBoard} />
                : <EmptyState message="The counseling board will open after you begin the conversation." />
            )}
          </>
        )}

      </div>
    </div>
  )
}


function BoardLoadingState() {
  return (
    <div className="p-6 space-y-5 animate-pulse-slow">
      {/* Identity hero skeleton */}
      <div className="rounded-2xl bg-sage-100 h-28 w-full" />

      {/* Section skeletons */}
      {[1, 2, 3].map((i) => (
        <div key={i} className="space-y-2">
          <div className="h-3 bg-sage-100 rounded w-1/3" />
          <div className="h-3 bg-sage-100 rounded w-full" />
          <div className="h-3 bg-sage-100 rounded w-5/6" />
        </div>
      ))}

      {/* Chips skeleton */}
      <div className="flex gap-2 flex-wrap pt-1">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-6 bg-sage-100 rounded-full w-16" />
        ))}
      </div>

      <div className="flex items-center justify-center gap-2 pt-4">
        <div className="relative w-8 h-8">
          <div className="absolute inset-0 rounded-full border-2 border-sage-200" />
          <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-sage-400 animate-spin" />
        </div>
        <span className="text-xs text-sage-400">Reading the stars…</span>
      </div>
    </div>
  )
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-full px-8 text-center">
      <span className="text-3xl mb-3">🌿</span>
      <p className="text-sage-400 text-sm leading-relaxed">{message}</p>
    </div>
  )
}
