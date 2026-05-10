import type { SajuReport } from '@/types/api'
import ElementChart from './ElementChart'
import ReportSection from './ReportSection'
import KeywordChip from '@/components/ui/KeywordChip'

type Props = {
  report: SajuReport
}

export default function SajuReportTab({ report }: Props) {
  return (
    <div className="px-5 py-6 space-y-6">
      {/* Title */}
      <div>
        <h2 className="text-base font-semibold text-sage-900">{report.title}</h2>
        <p className="mt-1 text-sm text-sage-500 leading-relaxed">{report.overall_summary}</p>
      </div>

      {/* Divider */}
      <div className="border-t border-sage-100" />

      {/* Five-element chart */}
      <div>
        <h3 className="text-xs font-semibold text-sage-500 uppercase tracking-wider mb-3">
          Five Elements
        </h3>
        <ElementChart
          elements={report.elements}
          dominant={report.dominant_elements}
          lacking={report.lacking_elements}
        />
      </div>

      {/* Keywords */}
      <div>
        <h3 className="text-xs font-semibold text-sage-500 uppercase tracking-wider mb-2">
          Core Keywords
        </h3>
        <div className="flex flex-wrap gap-1.5">
          {report.keywords.map((kw) => (
            <KeywordChip key={kw} label={kw} />
          ))}
        </div>
      </div>

      <div className="border-t border-sage-100" />

      {/* Report sections */}
      <div className="space-y-5">
        <ReportSection icon="🧠" title={report.personality.title} summary={report.personality.summary} />
        <ReportSection icon="💛" title={report.relationship_style.title} summary={report.relationship_style.summary} />
        <ReportSection icon="💼" title={report.career_style.title} summary={report.career_style.summary} />
        <ReportSection icon="🌊" title={report.emotional_pattern.title} summary={report.emotional_pattern.summary} />
      </div>

      <div className="border-t border-sage-100" />

      {/* Strengths */}
      <div>
        <h3 className="text-xs font-semibold text-sage-500 uppercase tracking-wider mb-2">
          Strengths
        </h3>
        <div className="flex flex-wrap gap-1.5">
          {report.strengths.map((s) => (
            <KeywordChip key={s} label={s} variant="strength" />
          ))}
        </div>
      </div>

      {/* Cautions */}
      <div>
        <h3 className="text-xs font-semibold text-sage-500 uppercase tracking-wider mb-2">
          Cautions
        </h3>
        <div className="flex flex-wrap gap-1.5">
          {report.cautions.map((c) => (
            <KeywordChip key={c} label={c} variant="caution" />
          ))}
        </div>
      </div>

      <div className="border-t border-sage-100" />

      {/* One-line verdict */}
      <div className="bg-sage-800 rounded-xl px-5 py-4">
        <p className="text-xs font-semibold text-sage-300 uppercase tracking-wider mb-1">Reading</p>
        <p className="text-sm font-medium text-warm-white leading-relaxed italic">
          "{report.one_line_verdict}"
        </p>
      </div>
    </div>
  )
}
