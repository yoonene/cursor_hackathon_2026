import type { InsightSummary } from '@/types/api'

const typeIcon: Record<InsightSummary['type'], string> = {
  general_reading: '💬',
  compatibility_result: '💞',
  fortune_flow: '🌊',
  timing_recommendation: '✦',
}

type Props = {
  insights: InsightSummary[]
}

export default function InsightChips({ insights }: Props) {
  if (insights.length === 0) return null

  return (
    <div className="space-y-2">
      <h3 className="text-xs font-semibold text-sage-500 uppercase tracking-wider">Insights So Far</h3>
      <div className="flex flex-col gap-1.5">
        {insights.map((ins) => (
          <div
            key={ins.id}
            className="flex items-center gap-2 rounded-xl bg-warm-white border border-sage-100 px-3 py-2"
          >
            <span className="text-sm">{typeIcon[ins.type]}</span>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-sage-800 truncate">{ins.label}</p>
              <p className="text-xs text-sage-400 truncate">{ins.short_summary}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
