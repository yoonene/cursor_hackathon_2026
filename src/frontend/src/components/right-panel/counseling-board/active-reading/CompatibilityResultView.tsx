import { useState, useEffect } from 'react'
import type { CompatibilityResultTemplate } from '@/types/api'
import KeywordChip from '@/components/ui/KeywordChip'
import { clsx } from 'clsx'

type Props = { data: CompatibilityResultTemplate }

const connectionStyle = {
  supportive: { color: 'text-emerald-600', bg: 'bg-emerald-50 border-emerald-200' },
  balanced:   { color: 'text-sage-600',    bg: 'bg-sage-50 border-sage-200' },
  tense:      { color: 'text-amber-600',   bg: 'bg-amber-50 border-amber-200' },
}

export default function CompatibilityResultView({ data }: Props) {
  const [displayScore, setDisplayScore] = useState(0)

  // Count-up animation
  useEffect(() => {
    const target = data.score
    const duration = 900
    const steps = 40
    const increment = target / steps
    let current = 0
    const interval = setInterval(() => {
      current = Math.min(current + increment, target)
      setDisplayScore(Math.round(current))
      if (current >= target) clearInterval(interval)
    }, duration / steps)
    return () => clearInterval(interval)
  }, [data.score])

  const conn = connectionStyle[data.connection.type]

  return (
    <div className="rounded-xl bg-warm-white border border-sage-100 px-5 py-5 space-y-4 shadow-sm">
      <div>
        <p className="text-xs font-semibold text-sage-500 uppercase tracking-wider mb-1">
          Compatibility
        </p>
        <h3 className="text-sm font-semibold text-sage-900">{data.title}</h3>
      </div>

      {/* Score */}
      <div className="flex items-center gap-4">
        <div className="flex flex-col items-center">
          <span className="text-4xl font-bold text-sage-800 tabular-nums">{displayScore}</span>
          <span className="text-xs text-sage-400 mt-0.5">/ 100</span>
        </div>
        <div>
          <p className="text-sm font-semibold text-sage-800">{data.label}</p>
          {/* People */}
          <div className="flex gap-2 mt-1">
            {data.people.map((p) => (
              <span key={p.name} className="text-xs text-sage-500">
                {p.name}{p.dominant_element ? ` · ${p.dominant_element}` : ''}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Score bar */}
      <div className="h-2 w-full bg-sage-100 rounded-full overflow-hidden">
        <div
          className="h-full bg-sage-600 rounded-full transition-all duration-1000"
          style={{ width: `${displayScore}%` }}
        />
      </div>

      {/* Connection type */}
      <div className={clsx('rounded-lg border px-3 py-2', conn.bg)}>
        <p className={clsx('text-xs font-medium', conn.color)}>{data.connection.label}</p>
      </div>

      {/* Strengths */}
      <div>
        <p className="text-xs font-semibold text-sage-500 uppercase tracking-wider mb-1.5">Strengths</p>
        <div className="flex flex-wrap gap-1.5">
          {data.strengths.map((s) => <KeywordChip key={s} label={s} variant="strength" />)}
        </div>
      </div>

      {/* Friction */}
      <div>
        <p className="text-xs font-semibold text-sage-500 uppercase tracking-wider mb-1.5">Watch out for</p>
        <div className="flex flex-wrap gap-1.5">
          {data.friction_points.map((f) => <KeywordChip key={f} label={f} variant="caution" />)}
        </div>
      </div>

      {/* Advice */}
      <div className="border-t border-sage-100 pt-3">
        <p className="text-xs text-sage-600 italic leading-relaxed">"{data.one_line_advice}"</p>
      </div>
    </div>
  )
}
