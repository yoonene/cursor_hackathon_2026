import type { ChartIdentity } from '@/types/api'

// Character images
import imgRat from '../../../resource/character/rat.png'
import imgCow from '../../../resource/character/cow.png'
import imgTiger from '../../../resource/character/tiger.png'
import imgRabbit from '../../../resource/character/rabbit.png'
import imgDragon from '../../../resource/character/dragon.png'
import imgSnake from '../../../resource/character/snake.png'
import imgHorse from '../../../resource/character/horse.png'
import imgGoat from '../../../resource/character/goat.png'
import imgMonkey from '../../../resource/character/monkey.png'
import imgChicken from '../../../resource/character/chicken.png'
import imgDog from '../../../resource/character/dog.png'
import imgPig from '../../../resource/character/pig.png'

// Element images
import imgTree from '../../../resource/elements/tree.png'
import imgFire from '../../../resource/elements/fire.png'
import imgEarth from '../../../resource/elements/earth.png'
import imgGold from '../../../resource/elements/gold.png'
import imgWater from '../../../resource/elements/water.png'

type Props = {
  identity: ChartIdentity
}

const ANIMAL_IMAGE: Record<string, string> = {
  rat: imgRat,
  ox: imgCow,
  cow: imgCow,
  tiger: imgTiger,
  rabbit: imgRabbit,
  dragon: imgDragon,
  snake: imgSnake,
  horse: imgHorse,
  goat: imgGoat,
  sheep: imgGoat,
  monkey: imgMonkey,
  rooster: imgChicken,
  chicken: imgChicken,
  dog: imgDog,
  pig: imgPig,
  boar: imgPig,
}

const ELEMENT_IMAGE: Record<string, string> = {
  wood: imgTree,
  fire: imgFire,
  earth: imgEarth,
  metal: imgGold,
  water: imgWater,
}

const ELEMENT_LABEL: Record<string, string> = {
  wood: 'Wood',
  fire: 'Fire',
  earth: 'Earth',
  metal: 'Metal',
  water: 'Water',
}

const THEME_STYLES: Record<string, { bg: string; hanja: string; label: string; master: string; border: string }> = {
  metal: {
    bg: 'bg-gradient-to-br from-slate-100 to-slate-50',
    hanja: 'text-slate-700',
    label: 'text-slate-600',
    master: 'text-slate-500',
    border: 'border-slate-200',
  },
  wood: {
    bg: 'bg-gradient-to-br from-emerald-50 to-green-50',
    hanja: 'text-emerald-800',
    label: 'text-emerald-700',
    master: 'text-emerald-600',
    border: 'border-emerald-100',
  },
  fire: {
    bg: 'bg-gradient-to-br from-red-50 to-orange-50',
    hanja: 'text-red-700',
    label: 'text-red-600',
    master: 'text-red-500',
    border: 'border-red-100',
  },
  earth: {
    bg: 'bg-gradient-to-br from-amber-50 to-yellow-50',
    hanja: 'text-amber-800',
    label: 'text-amber-700',
    master: 'text-amber-600',
    border: 'border-amber-100',
  },
  water: {
    bg: 'bg-gradient-to-br from-blue-50 to-sky-50',
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

  const animalImg = ANIMAL_IMAGE[visual_tokens.animal]
  const elementImg = ELEMENT_IMAGE[visual_tokens.theme]
  const elementLabel = ELEMENT_LABEL[visual_tokens.theme] ?? visual_tokens.theme

  return (
    <div className={`rounded-xl border ${style.border} ${style.bg} px-5 py-5`}>
      <div className="flex items-center gap-4">
        {/* 이미지: 오행(왼쪽) + 동물(오른쪽) 나란히 */}
        {elementImg && (
          <img
            src={elementImg}
            alt={elementLabel}
            className="w-12 h-12 object-contain shrink-0"
          />
        )}
        {animalImg && (
          <img
            src={animalImg}
            alt={day_pillar.animal_label}
            className="w-[72px] h-[72px] object-contain shrink-0"
          />
        )}

        {/* 텍스트 */}
        <div className="flex flex-col justify-center gap-1">
          <p className={`text-lg font-semibold ${style.label}`}>
            {day_pillar.english_name}
          </p>
          <p className={`text-xs font-medium uppercase tracking-widest ${style.master}`}>
            {elementLabel} · {day_master.english_name}
          </p>
        </div>
      </div>
    </div>
  )
}
