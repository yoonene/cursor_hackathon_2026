import type { FortuneFlowTemplate, ElementTone } from '@/types/api'

type Props = { data: FortuneFlowTemplate }

const toneStyle: Record<ElementTone, string> = {
  muted:     'bg-sage-50 text-sage-400 border-sage-100',
  soft:      'bg-sage-100 text-sage-600 border-sage-200',
  highlight: 'bg-sage-200 text-sage-800 border-sage-300 font-semibold',
  strong:    'bg-sage-600 text-white border-sage-600 font-semibold',
}

const domainIcon: Record<string, string> = {
  love: '💛', career: '💼', money: '💰', relationships: '🤝', health: '🌱', overall: '✦',
}

const periodLabel: Record<string, string> = {
  today: 'Today', this_week: 'This Week', this_month: 'This Month', current_phase: 'Current Phase',
}

export default function FortuneFlowView({ data }: Props) {
  return (
    <div className="rounded-xl bg-warm-white border border-sage-100 px-5 py-5 space-y-4 shadow-sm">
      {/* Header */}
      <div>
        <p className="text-xs font-semibold text-sage-500 uppercase tracking-wider mb-1">
          {domainIcon[data.domain]} {periodLabel[data.period]} · {data.domain}
        </p>
        <h3 className="text-sm font-semibold text-sage-900">{data.title}</h3>
      </div>

      {/* Headline keyword */}
      <div className="flex items-center gap-2">
        <span className="text-2xl font-bold text-sage-800">{data.headline_keyword}</span>
      </div>

      <p className="text-sm text-sage-700 leading-relaxed">{data.one_line_summary}</p>

      {/* Timeline segments */}
      {data.segments.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-sage-500 uppercase tracking-wider mb-2">Flow</p>
          <div className="flex gap-1.5">
            {data.segments.map((seg, i) => (
              <div
                key={i}
                className={`flex-1 rounded-xl border px-2 py-2.5 text-center transition-all ${
                  toneStyle[seg.tone ?? 'soft']
                }`}
              >
                <p className="text-xs leading-none mb-1 opacity-70">{seg.label}</p>
                <p className="text-xs font-medium leading-tight">{seg.keyword}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommended action */}
      {data.recommended_action && (
        <div className="rounded-lg bg-sage-50 border border-sage-200 px-4 py-2.5">
          <p className="text-xs text-sage-600">
            <span className="font-semibold text-sage-700">Suggestion · </span>
            {data.recommended_action}
          </p>
        </div>
      )}
    </div>
  )
}
