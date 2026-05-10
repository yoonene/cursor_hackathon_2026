import { useSessionStore } from '@/store/sessionStore'
import FateMeLogo from '@/components/ui/FateMeLogo'

export default function LandingPage() {
  const goToIntake = useSessionStore((s) => s.goToIntake)

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-sage-50">
      {/* Full-screen logo */}
      <FateMeLogo
        fullScreen
        className="absolute inset-0 w-full h-full"
      />

      {/* Start button — always on top */}
      <div className="absolute inset-0 flex items-end justify-center pb-20 z-10">
        <button
          onClick={goToIntake}
          className="px-10 py-3 rounded-full bg-sage-600 text-white text-sm font-semibold tracking-wide hover:bg-sage-700 active:bg-sage-800 transition-colors shadow-sm"
        >
          Start
        </button>
      </div>
    </div>
  )
}
