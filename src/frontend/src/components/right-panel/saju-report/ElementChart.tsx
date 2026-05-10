import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip } from 'recharts'
import type { ElementMap } from '@/types/api'

type Props = {
  elements: ElementMap
  dominant: string[]
  lacking: string[]
}

const ELEMENT_CONFIG = {
  wood:  { label: 'Wood',  color: '#4ade80' },
  fire:  { label: 'Fire',  color: '#f87171' },
  earth: { label: 'Earth', color: '#fbbf24' },
  metal: { label: 'Metal', color: '#94a3b8' },
  water: { label: 'Water', color: '#60a5fa' },
}

export default function ElementChart({ elements, dominant, lacking }: Props) {
  const data = Object.entries(elements).map(([key, value]) => ({
    element: ELEMENT_CONFIG[key as keyof ElementMap].label,
    value,
    fullMark: 6,
  }))

  return (
    <div className="space-y-3">
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={data} margin={{ top: 8, right: 20, bottom: 8, left: 20 }}>
            <PolarGrid stroke="#c8d9c8" />
            <PolarAngleAxis
              dataKey="element"
              tick={{ fontSize: 11, fill: '#4a7c59', fontWeight: 500 }}
            />
            <Tooltip
              contentStyle={{
                background: '#fafaf8',
                border: '1px solid #c8d9c8',
                borderRadius: 10,
                fontSize: 12,
              }}
            />
            <Radar
              dataKey="value"
              stroke="#4a7c59"
              fill="#4a7c59"
              fillOpacity={0.25}
              strokeWidth={2}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Legend row */}
      <div className="flex flex-wrap gap-2">
        {Object.entries(elements).map(([key, val]) => {
          const cfg = ELEMENT_CONFIG[key as keyof ElementMap]
          const isDominant = dominant.includes(key)
          const isLacking = lacking.includes(key)
          return (
            <div
              key={key}
              className="flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium border"
              style={{
                borderColor: isDominant ? cfg.color : isLacking ? '#e5e7eb' : '#e4ece4',
                background: isDominant ? `${cfg.color}18` : isLacking ? '#f9fafb' : '#f4f7f4',
                color: isDominant ? cfg.color : isLacking ? '#9ca3af' : '#4a7c59',
              }}
            >
              <span
                className="w-2 h-2 rounded-full"
                style={{ background: cfg.color }}
              />
              {cfg.label} {val}
              {isDominant && <span className="ml-0.5">↑</span>}
              {isLacking && <span className="ml-0.5 opacity-60">↓</span>}
            </div>
          )
        })}
      </div>
    </div>
  )
}
