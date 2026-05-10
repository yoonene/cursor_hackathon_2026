import { clsx } from 'clsx'

type Props = {
  label: string
  variant?: 'default' | 'strength' | 'caution' | 'muted'
}

const variantClass = {
  default:  'bg-sage-100 text-sage-700 border-sage-200',
  strength: 'bg-sage-600 text-white border-sage-600',
  caution:  'bg-amber-100 text-amber-800 border-amber-200',
  muted:    'bg-sage-50 text-sage-400 border-sage-100',
}

export default function KeywordChip({ label, variant = 'default' }: Props) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium',
        variantClass[variant]
      )}
    >
      {label}
    </span>
  )
}
