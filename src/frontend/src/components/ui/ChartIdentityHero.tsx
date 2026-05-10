import type { ChartIdentity } from '@/types/api'

type Props = {
  identity: ChartIdentity
}

const ANIMAL_EMOJI: Record<string, string> = {
  rabbit: '🐇', tiger: '🐯', dragon: '🐉', snake: '🐍', horse: '🐎',
  goat: '🐑', monkey: '🐒', rooster: '🐓', dog: '🐕', pig: '🐖',
  rat: '🐀', ox: '🐂',
}

const THEME_STYLES: Record<string, { bg: string; hanja: string; label: string; master: string; border: string }> = {
  metal: {
    bg: 'bg-gradient-to-b from-slate-100 to-sage-50',
    hanja: 'text-slate-700',
    label: 'text-slate-600',
    master: 'text-slate-500',
    border: 'border-slate-200',
  },
  wood: {
    bg: 'bg-gradient-to-b from-emerald-50 to-sage-50',
    hanja: 'text-emerald-800',
    label: 'text-emerald-700',
    master: 'text-emerald-600',
    border: 'border-emerald-100',
  },
  fire: {
    bg: 'bg-gradient-to-b from-red-50 to-sage-50',
    hanja: 'text-red-700',
    label: 'text-red-600',
    master: 'text-red-500',
    border: 'border-red-100',
  },
  earth: {
    bg: 'bg-gradient-to-b from-amber-50 to-sage-50',
    hanja: 'text-amber-800',
    label: 'text-amber-700',
    master: 'text-amber-600',
    border: 'border-amber-100',
  },
  water: {
    bg: 'bg-gradient-to-b from-blue-50 to-sage-50',
    hanja: 'text-blue-700',
    label: 'text-blue-600',
    master: 'text-blue-500',
    border: 'border-blue-100',
  },
}

const DEFAULT_STYLE = THEME_STYLES.metal

export default function ChartIdentityHero({ identity }: Props) {
  const { day_pillar, day_master, visual_tokens } = identity
  const style = THEME_STYLES[visual_tokens.theme] ?? DEFAULT_STYLE
  const animalEmoji = ANIMAL_EMOJI[visual_tokens.animal] ?? '✦'

  return (
    <div className={`rounded-xl border ${style.border} ${style.bg} px-5 py-6 text-center space-y-2`}>
      {/* Animal + Hanja */}
      <div className="flex items-center justify-center gap-2">
        <span className="text-2xl" role="img" aria-label={day_pillar.animal_label}>
          {animalEmoji}
        </span>
        <span className={`text-4xl font-bold tracking-widest ${style.hanja}`}>
          {day_pillar.ganji_hanja}
        </span>
      </div>

      {/* English name */}
      <p className={`text-base font-semibold ${style.label}`}>
        {day_pillar.english_name}
      </p>

      {/* Day master */}
      <p className={`text-xs font-medium uppercase tracking-widest ${style.master}`}>
        Day Master · {day_master.display_label}
      </p>
    </div>
  )
}
