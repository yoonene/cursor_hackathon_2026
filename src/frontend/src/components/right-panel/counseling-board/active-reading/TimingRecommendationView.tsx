import type { TimingRecommendationTemplate, ElementTone } from '@/types/api'

type Props = { data: TimingRecommendationTemplate }

const toneStyle: Record<ElementTone, string> = {
  muted:     'bg-sage-50 text-sage-400 border-sage-100',
  soft:      'bg-sage-100 text-sage-600 border-sage-200',
  highlight: 'bg-sage-200 text-sage-800 border-sage-300 font-semibold',
  strong:    'bg-sage-600 text-white border-sage-600 font-semibold',
}

export default function TimingRecommendationView({ data }: Props) {
  return (
    <div className="rounded-xl bg-warm-white border border-sage-100 px-5 py-5 space-y-4 shadow-sm">
      {/* Header */}
      <div>
        <p className="text-xs font-semibold text-sage-500 uppercase tracking-wider mb-1">
          ✦ Best Timing · {data.domain}
        </p>
        <h3 className="text-sm font-semibold text-sage-900">{data.title}</h3>
      </div>

      {/* Headline keyword */}
      <span className="text-2xl font-bold text-sage-800">{data.headline_keyword}</span>

      <p className="text-sm text-sage-700 leading-relaxed">{data.one_line_summary}</p>

      {/* Recommended window */}
      <div className="rounded-xl border-2 border-sage-600 bg-sage-50 px-4 py-3 space-y-1">
        <p className="text-xs font-semibold text-sage-600 uppercase tracking-wider">
          {data.recommended_window.label}
        </p>
        <p className="text-base font-bold text-sage-800">{data.recommended_window.date_range}</p>
        <p className="text-xs text-sage-600 leading-relaxed">{data.recommended_window.reason}</p>
      </div>

      {/* Timeline */}
      {data.timeline && data.timeline.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-sage-500 uppercase tracking-wider mb-2">Flow</p>
          <div className="flex gap-1.5">
            {data.timeline.map((seg, i) => (
              <div
                key={i}
                className={`flex-1 rounded-xl border px-2 py-2.5 text-center ${
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

      {/* Caution window */}
      {data.caution_window && (
        <div className="rounded-lg bg-amber-50 border border-amber-200 px-4 py-2.5 space-y-0.5">
          <p className="text-xs font-semibold text-amber-700 uppercase tracking-wider">
            {data.caution_window.label} · {data.caution_window.date_range}
          </p>
          <p className="text-xs text-amber-700 leading-relaxed">{data.caution_window.reason}</p>
        </div>
      )}
    </div>
  )
}
