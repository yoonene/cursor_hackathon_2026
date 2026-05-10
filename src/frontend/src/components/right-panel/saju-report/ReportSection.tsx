type Props = {
  title: string
  summary: string
  icon?: string
}

export default function ReportSection({ title, summary, icon }: Props) {
  return (
    <div className="space-y-1.5">
      <h3 className="flex items-center gap-1.5 text-xs font-semibold text-sage-500 uppercase tracking-wider">
        {icon && <span>{icon}</span>}
        {title}
      </h3>
      <p className="text-sm text-sage-800 leading-relaxed">{summary}</p>
    </div>
  )
}
