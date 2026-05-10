import { useState } from 'react'
import { useSessionStore } from '@/store/sessionStore'
import type { Gender } from '@/types/api'

const genderOptions: { value: Gender; label: string }[] = [
  { value: 'female', label: 'Female' },
  { value: 'male', label: 'Male' },
  { value: 'other', label: 'Other' },
  { value: 'prefer_not_to_say', label: 'Prefer not to say' },
]

export default function IntakeForm() {
  const submitIntake = useSessionStore((s) => s.submitIntake)
  const isLoading = useSessionStore((s) => s.isLoading)
  const error = useSessionStore((s) => s.error)

  const [displayName, setDisplayName] = useState('')
  const [birthDate, setBirthDate] = useState('')
  const [birthTime, setBirthTime] = useState('')
  const [gender, setGender] = useState<Gender | ''>('')

  const canSubmit = birthDate.trim() !== '' && !isLoading

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!canSubmit) return
    submitIntake({
      display_name: displayName.trim() || undefined,
      birth_date: birthDate,
      birth_time: birthTime || undefined,
      gender: gender || undefined,
    })
  }

  return (
    <div className="w-full max-w-md">
      {/* Header */}
      <div className="text-center mb-10">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-sage-100 mb-4">
          <span className="text-2xl">🌿</span>
        </div>
        <h1 className="text-3xl tracking-tight">
          <span className="font-bold text-sage-900">Fate</span>
          <span className="font-light text-sage-400">.me</span>
        </h1>
        <p className="mt-2 text-sage-500 text-sm leading-relaxed">
          Share when you were born and I will begin your reading.
        </p>
      </div>

      {/* Form card */}
      <form
        onSubmit={handleSubmit}
        className="bg-warm-white rounded-2xl p-8 shadow-sm border border-sage-100 space-y-6"
      >
        {/* Name */}
        <div className="space-y-1.5">
          <label className="block text-sm font-medium text-sage-700">
            Name or nickname
            <span className="ml-1 text-sage-400 font-normal">(optional)</span>
          </label>
          <input
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="e.g. Yoon"
            className="w-full rounded-xl border border-sage-200 bg-sage-50 px-4 py-2.5 text-sm text-sage-900 placeholder:text-sage-300 focus:outline-none focus:ring-2 focus:ring-sage-400 focus:border-transparent transition"
          />
        </div>

        {/* Birth date */}
        <div className="space-y-1.5">
          <label className="block text-sm font-medium text-sage-700">
            Date of birth
            <span className="ml-1 text-red-400">*</span>
          </label>
          <input
            type="date"
            value={birthDate}
            onChange={(e) => setBirthDate(e.target.value)}
            required
            className="w-full rounded-xl border border-sage-200 bg-sage-50 px-4 py-2.5 text-sm text-sage-900 focus:outline-none focus:ring-2 focus:ring-sage-400 focus:border-transparent transition"
          />
        </div>

        {/* Birth time */}
        <div className="space-y-1.5">
          <label className="block text-sm font-medium text-sage-700">
            Time of birth
            <span className="ml-1 text-sage-400 font-normal">(optional)</span>
          </label>
          <input
            type="time"
            value={birthTime}
            onChange={(e) => setBirthTime(e.target.value)}
            className="w-full rounded-xl border border-sage-200 bg-sage-50 px-4 py-2.5 text-sm text-sage-900 focus:outline-none focus:ring-2 focus:ring-sage-400 focus:border-transparent transition"
          />
          <p className="text-xs text-sage-400">A more precise reading is possible with your birth time.</p>
        </div>

        {/* Gender */}
        <div className="space-y-1.5">
          <label className="block text-sm font-medium text-sage-700">
            Gender
            <span className="ml-1 text-sage-400 font-normal">(optional)</span>
          </label>
          <div className="grid grid-cols-2 gap-2">
            {genderOptions.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setGender(gender === opt.value ? '' : opt.value)}
                className={`rounded-xl border px-3 py-2 text-sm font-medium transition ${
                  gender === opt.value
                    ? 'bg-sage-600 text-white border-sage-600'
                    : 'bg-sage-50 text-sage-600 border-sage-200 hover:border-sage-400'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Error */}
        {error && (
          <p className="text-sm text-red-500 text-center">{error}</p>
        )}

        {/* Submit */}
        <button
          type="submit"
          disabled={!canSubmit}
          className="w-full rounded-xl bg-sage-600 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-sage-700 active:bg-sage-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
              Reading your chart…
            </span>
          ) : (
            'Begin Reading'
          )}
        </button>
      </form>

      <p className="mt-6 text-center text-xs text-sage-400">
        Your information is only used for this reading session.
      </p>
    </div>
  )
}
