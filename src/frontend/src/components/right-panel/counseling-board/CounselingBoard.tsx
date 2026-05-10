import type { CounselingBoard as CounselingBoardType } from '@/types/api'
import ProfileSummary from './ProfileSummary'
import InsightChips from './InsightChips'
import ActiveReading from './active-reading/ActiveReading'

type Props = {
  board: CounselingBoardType
}

export default function CounselingBoard({ board }: Props) {
  return (
    <div className="px-5 py-6 space-y-5">
      {/* 1. Base Flow Summary */}
      {board.profile_summary && (
        <ProfileSummary summary={board.profile_summary} />
      )}

      {/* 2. Current Reading */}
      {board.active_reading ? (
        <ActiveReading reading={board.active_reading} />
      ) : (
        <div className="rounded-xl border border-dashed border-sage-200 px-4 py-8 flex flex-col items-center text-center gap-2">
          <span className="text-2xl">✦</span>
          <p className="text-xs text-sage-400 leading-relaxed">
            The current reading focus will appear here as the conversation continues.
          </p>
        </div>
      )}

      {/* 3. Insights So Far */}
      <InsightChips insights={board.insight_summaries} />
    </div>
  )
}
