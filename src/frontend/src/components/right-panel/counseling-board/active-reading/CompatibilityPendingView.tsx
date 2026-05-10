import type { CompatibilityPendingTemplate } from '@/types/api'

type Props = { data: CompatibilityPendingTemplate }

export default function CompatibilityPendingView({ data }: Props) {
  return (
    <div className="rounded-xl bg-warm-white border border-sage-100 px-5 py-5 space-y-5 shadow-sm">
      <div>
        <p className="text-xs font-semibold text-sage-500 uppercase tracking-wider mb-1">
          Compatibility
        </p>
        <h3 className="text-sm font-semibold text-sage-900">{data.title}</h3>
      </div>

      {/* Two nodes */}
      <div className="flex items-center justify-center gap-4 py-2">
        <PersonNode name={data.left_person.name} />

        {/* Animated connecting line */}
        <div className="flex-1 relative h-px">
          <div className="absolute inset-0 bg-gradient-to-r from-sage-300 via-sage-500 to-sage-300 rounded-full animate-pulse" />
          <div
            className="absolute top-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-sage-500 animate-ping"
            style={{ left: '45%' }}
          />
        </div>

        <PersonNode name={data.right_person?.name ?? '?'} faded={!data.right_person?.name} />
      </div>

      {/* Status */}
      <p className="text-sm text-sage-600 text-center italic">{data.status_message}</p>

      {/* Missing fields hint */}
      {data.missing_fields && data.missing_fields.length > 0 && (
        <div className="rounded-lg bg-sage-50 border border-sage-100 px-4 py-2.5">
          <p className="text-xs text-sage-500">
            Still needed: <span className="font-medium text-sage-700">{data.missing_fields.join(', ')}</span>
          </p>
        </div>
      )}
    </div>
  )
}

function PersonNode({ name, faded = false }: { name: string; faded?: boolean }) {
  return (
    <div className={`flex flex-col items-center gap-1.5 transition-opacity ${faded ? 'opacity-40' : ''}`}>
      <div className="w-12 h-12 rounded-full bg-sage-100 border-2 border-sage-300 flex items-center justify-center text-lg font-semibold text-sage-700">
        {name === '?' ? '?' : name.charAt(0).toUpperCase()}
      </div>
      <span className="text-xs text-sage-600 font-medium">{name}</span>
    </div>
  )
}
