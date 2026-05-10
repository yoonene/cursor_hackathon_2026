import type { ChartIdentitySummary } from '@/types/api'

type Props = {
  summary: ChartIdentitySummary
}

export default function ChartIdentityBadge({ summary }: Props) {
  return (
    <p className="text-xs text-sage-500 font-medium tracking-wide">
      {summary.day_pillar_label} · {summary.day_master_label}
    </p>
  )
}
