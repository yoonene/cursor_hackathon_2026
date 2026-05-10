import type { ActiveReading as ActiveReadingType } from '@/types/api'
import GeneralReadingView from './GeneralReadingView'
import CompatibilityPendingView from './CompatibilityPendingView'
import CompatibilityResultView from './CompatibilityResultView'
import FortuneFlowView from './FortuneFlowView'
import TimingRecommendationView from './TimingRecommendationView'

type Props = {
  reading: ActiveReadingType
}

export default function ActiveReading({ reading }: Props) {
  switch (reading.template) {
    case 'general_reading':
      return <GeneralReadingView data={reading} />
    case 'compatibility_pending':
      return <CompatibilityPendingView data={reading} />
    case 'compatibility_result':
      return <CompatibilityResultView data={reading} />
    case 'fortune_flow':
      return <FortuneFlowView data={reading} />
    case 'timing_recommendation':
      return <TimingRecommendationView data={reading} />
    default:
      return null
  }
}
