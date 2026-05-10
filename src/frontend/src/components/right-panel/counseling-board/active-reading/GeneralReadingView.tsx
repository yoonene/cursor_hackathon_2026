import type { GeneralReadingTemplate } from '@/types/api'
import KeywordChip from '@/components/ui/KeywordChip'

type Props = { data: GeneralReadingTemplate }

export default function GeneralReadingView({ data }: Props) {
  return (
    <div className="rounded-xl bg-warm-white border border-sage-100 px-5 py-5 space-y-3 shadow-sm">
      <div>
        <p className="text-xs font-semibold text-sage-500 uppercase tracking-wider mb-1">
          Current Reading
        </p>
        <h3 className="text-sm font-semibold text-sage-900">{data.title}</h3>
        {data.headline && (
          <p className="text-xs text-sage-500 mt-0.5">{data.headline}</p>
        )}
      </div>

      <p className="text-sm text-sage-800 leading-relaxed">{data.body}</p>

      {data.highlighted_traits && data.highlighted_traits.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {data.highlighted_traits.map((t) => (
            <KeywordChip key={t} label={t} />
          ))}
        </div>
      )}

      {data.prompt_to_user && (
        <p className="text-xs text-sage-500 italic border-t border-sage-100 pt-3">
          {data.prompt_to_user}
        </p>
      )}
    </div>
  )
}
