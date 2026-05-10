import { useState } from 'react'
import { useSessionStore } from '@/store/sessionStore'
import type { Gender } from '@/types/api'

export default function PartnerIntakeModal() {
  const submitPartner = useSessionStore((s) => s.submitPartner)
  const closePartnerIntake = useSessionStore((s) => s.closePartnerIntake)
  const isLoading = useSessionStore((s) => s.isLoading)

  const [displayName, setDisplayName] = useState('')
  const [birthDate, setBirthDate] = useState('')
  const [birthTime, setBirthTime] = useState('')
  const [gender, setGender] = useState<Gender | ''>('')
  const [error, setError] = useState('')

  const handleSubmit = () => {
    if (!birthDate) {
      setError('Please enter the date of birth.')
      return
    }
    setError('')
    submitPartner({
      display_name: displayName.trim() || null,
      birth_date: birthDate,
      birth_time: birthTime || null,
      gender: (gender as Gender) || null,
    })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="bg-warm-white rounded-2xl shadow-xl w-full max-w-sm mx-4 p-6 space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-sage-900">Partner's Information</h2>
            <p className="text-xs text-sage-400 mt-0.5">Enter their birth details for compatibility reading</p>
          </div>
          <button
            onClick={closePartnerIntake}
            className="text-sage-400 hover:text-sage-600 transition-colors p-1"
            aria-label="Close"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Fields */}
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-sage-700 mb-1">
              Name <span className="text-sage-400 font-normal">(optional)</span>
            </label>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="e.g. Minsoo"
              maxLength={80}
              className="w-full rounded-lg border border-sage-200 bg-sage-50 px-3 py-2 text-sm text-sage-900 placeholder:text-sage-300 focus:outline-none focus:ring-2 focus:ring-sage-400 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-sage-700 mb-1">
              Date of Birth <span className="text-red-400">*</span>
            </label>
            <input
              type="date"
              value={birthDate}
              onChange={(e) => setBirthDate(e.target.value)}
              className="w-full rounded-lg border border-sage-200 bg-sage-50 px-3 py-2 text-sm text-sage-900 focus:outline-none focus:ring-2 focus:ring-sage-400 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-sage-700 mb-1">
              Time of Birth <span className="text-sage-400 font-normal">(optional)</span>
            </label>
            <input
              type="time"
              value={birthTime}
              onChange={(e) => setBirthTime(e.target.value)}
              className="w-full rounded-lg border border-sage-200 bg-sage-50 px-3 py-2 text-sm text-sage-900 focus:outline-none focus:ring-2 focus:ring-sage-400 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-sage-700 mb-1">
              Gender <span className="text-sage-400 font-normal">(optional)</span>
            </label>
            <select
              value={gender}
              onChange={(e) => setGender(e.target.value as Gender | '')}
              className="w-full rounded-lg border border-sage-200 bg-sage-50 px-3 py-2 text-sm text-sage-900 focus:outline-none focus:ring-2 focus:ring-sage-400 focus:border-transparent"
            >
              <option value="">Select...</option>
              <option value="female">Female</option>
              <option value="male">Male</option>
              <option value="other">Other</option>
              <option value="prefer_not_to_say">Prefer not to say</option>
            </select>
          </div>
        </div>

        {error && (
          <p className="text-xs text-red-500">{error}</p>
        )}

        {/* Actions */}
        <div className="flex gap-2 pt-1">
          <button
            onClick={closePartnerIntake}
            className="flex-1 rounded-lg border border-sage-200 py-2 text-sm text-sage-600 hover:bg-sage-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={isLoading || !birthDate}
            className="flex-1 rounded-lg bg-sage-600 py-2 text-sm text-white hover:bg-sage-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? 'Reading...' : 'Check Compatibility'}
          </button>
        </div>
      </div>
    </div>
  )
}
