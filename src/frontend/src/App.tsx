import { useSessionStore } from '@/store/sessionStore'
import MainPage from '@/pages/MainPage'

export default function App() {
  const phase = useSessionStore((s) => s.phase)

  return (
    <div className="min-h-screen bg-sage-50">
      <MainPage phase={phase} />
    </div>
  )
}
