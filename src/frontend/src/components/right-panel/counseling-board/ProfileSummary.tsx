import type { ProfileSummary as ProfileSummaryType } from '@/types/api'
import KeywordChip from '@/components/ui/KeywordChip'
import ChartIdentityBadge from '@/components/ui/ChartIdentityBadge'

type Props = {
  summary: ProfileSummaryType
}

const ELEMENT_COLORS: Record<string, string> = {
  wood: '#4ade80', fire: '#f87171', earth: '#fbbf24', metal: '#94a3b8', water: '#60a5fa',
}

export default function ProfileSummary({ summary }: Props) {
  return (
    <div className="bg-warm-white border border-sage-100 rounded-xl px-4 py-3 space-y-2.5">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-sage-500 uppercase tracking-wider">Base Flow</span>
        <span className="text-xs text-sage-400">{summary.title}</span>
      </div>

      <p className="text-sm text-sage-800 leading-snug">{summary.one_line_summary}</p>

      {/* Chart identity — compact badge, shown only when backend provides the new field */}
      {summary.chart_identity_summary && (
        <ChartIdentityBadge summary={summary.chart_identity_summary} />
      )}

      {/* Element mini bars */}
      <div className="flex gap-1 items-end h-5">
        {Object.entries(summary.elements).map(([key, val]) => (
          <div
            key={key}
            title={`${key}: ${val}`}
            className="flex-1 rounded-sm transition-all"
            style={{
              height: `${(val / 6) * 100}%`,
              minHeight: 4,
              background: ELEMENT_COLORS[key] ?? '#c8d9c8',
              opacity: summary.dominant_elements.includes(key) ? 1 : 0.45,
            }}
          />
        ))}
      </div>

      {/* Keywords */}
      <div className="flex flex-wrap gap-1">
        {summary.keywords.map((kw) => (
          <KeywordChip key={kw} label={kw} variant="muted" />
        ))}
      </div>
    </div>
  )
}
