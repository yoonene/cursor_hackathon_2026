import { clsx } from 'clsx'

type Element = 'wood' | 'fire' | 'earth' | 'metal' | 'water'

const config: Record<Element, { label: string; emoji: string; className: string }> = {
  wood:  { label: 'Wood',  emoji: '🌿', className: 'bg-emerald-100 text-emerald-800 border-emerald-200' },
  fire:  { label: 'Fire',  emoji: '🔥', className: 'bg-red-100 text-red-700 border-red-200' },
  earth: { label: 'Earth', emoji: '🪨', className: 'bg-amber-100 text-amber-800 border-amber-200' },
  metal: { label: 'Metal', emoji: '✦',  className: 'bg-slate-100 text-slate-700 border-slate-200' },
  water: { label: 'Water', emoji: '💧', className: 'bg-blue-100 text-blue-700 border-blue-200' },
}

type Props = {
  element: Element
  size?: 'sm' | 'md'
  showEmoji?: boolean
}

export default function ElementBadge({ element, size = 'md', showEmoji = true }: Props) {
  const { label, emoji, className } = config[element]
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 rounded-full border font-medium',
        size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm',
        className
      )}
    >
      {showEmoji && <span>{emoji}</span>}
      {label}
    </span>
  )
}
