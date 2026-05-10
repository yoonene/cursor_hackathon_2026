// ─── Enums ───────────────────────────────────────────────────────────────────

export type CurrentStage =
  | 'initial_report'
  | 'open_counseling'
  | 'collecting_compatibility_info'
  | 'collecting_tool_inputs'

export type RecommendedTab = 'saju_report' | 'counseling_board'

export type ActiveTemplate =
  | 'general_reading'
  | 'compatibility_pending'
  | 'compatibility_result'
  | 'fortune_flow'
  | 'timing_recommendation'

export type ElementTone = 'muted' | 'soft' | 'highlight' | 'strong'

export type Gender = 'female' | 'male' | 'other' | 'prefer_not_to_say'

// ─── Request types ────────────────────────────────────────────────────────────

export type StartReadingRequest = {
  session_id: string
  display_name?: string
  birth_date: string
  birth_time?: string
  gender?: Gender
}

export type PartnerCompatibilityPayload = {
  display_name?: string | null
  birth_date: string
  birth_time?: string | null
  gender?: Gender | null
}

export type ChatRequest = {
  session_id: string
  message?: string
  partner?: PartnerCompatibilityPayload | null
}

export type SessionResetRequest = {
  session_id: string
}

// ─── Chart Identity ───────────────────────────────────────────────────────────

export type DayPillarIdentity = {
  ganji_hanja: string
  ganji_hangul: string
  stem_hanja: string
  branch_hanja: string
  english_name: string
  animal: string
  animal_label: string
  color: string
}

export type DayMasterIdentity = {
  stem_hanja: string
  stem_hangul: string
  element: string
  element_label: string
  polarity: string
  english_name: string
  display_label: string
}

export type ChartVisualTokens = {
  theme: string
  accent: string
  animal: string
}

export type ChartIdentity = {
  day_pillar: DayPillarIdentity
  day_master: DayMasterIdentity
  visual_tokens: ChartVisualTokens
}

export type ChartIdentitySummary = {
  day_pillar_hanja: string
  day_pillar_label: string
  day_master_label: string
  display_label: string
  theme: string
  accent: string
  animal: string
}

// ─── Saju Report ─────────────────────────────────────────────────────────────

export type ReportSection = {
  title: string
  summary: string
}

export type ElementMap = {
  wood: number
  fire: number
  earth: number
  metal: number
  water: number
}

export type SajuReport = {
  id: string
  title: string
  overall_summary: string
  elements: ElementMap
  dominant_elements: string[]
  lacking_elements: string[]
  keywords: string[]
  personality: ReportSection
  relationship_style: ReportSection
  career_style: ReportSection
  emotional_pattern: ReportSection
  strengths: string[]
  cautions: string[]
  one_line_verdict: string
  chart_identity?: ChartIdentity
}

// ─── Active Reading Templates ─────────────────────────────────────────────────

export type GeneralReadingTemplate = {
  id: string
  semantic_key: string
  template: 'general_reading'
  title: string
  headline?: string
  body: string
  highlighted_traits?: string[]
  prompt_to_user?: string
}

export type CompatibilityPendingTemplate = {
  id: string
  semantic_key: string
  template: 'compatibility_pending'
  title: string
  left_person: { name: string }
  right_person?: { name?: string }
  status_message: string
  missing_fields?: string[]
}

export type CompatibilityResultTemplate = {
  id: string
  semantic_key: string
  template: 'compatibility_result'
  title: string
  score: number
  label: string
  people: Array<{ name: string; dominant_element?: string }>
  connection: {
    type: 'supportive' | 'balanced' | 'tense'
    label: string
  }
  strengths: string[]
  friction_points: string[]
  one_line_advice: string
}

export type TimelineSegment = {
  label: string
  keyword: string
  tone?: ElementTone
}

export type FortuneFlowTemplate = {
  id: string
  semantic_key: string
  template: 'fortune_flow'
  title: string
  domain: 'love' | 'career' | 'money' | 'relationships' | 'health' | 'overall'
  period: 'today' | 'this_week' | 'this_month' | 'current_phase'
  headline_keyword: string
  one_line_summary: string
  segments: TimelineSegment[]
  recommended_action?: string
}

export type TimingWindow = {
  label: string
  date_range: string
  reason: string
}

export type TimingRecommendationTemplate = {
  id: string
  semantic_key: string
  template: 'timing_recommendation'
  title: string
  domain: 'love' | 'career' | 'money' | 'relationships' | 'health' | 'general'
  action_type: string
  headline_keyword: string
  one_line_summary: string
  recommended_window: TimingWindow
  timeline?: TimelineSegment[]
  caution_window?: TimingWindow
}

export type ActiveReading =
  | GeneralReadingTemplate
  | CompatibilityPendingTemplate
  | CompatibilityResultTemplate
  | FortuneFlowTemplate
  | TimingRecommendationTemplate

// ─── Counseling Board ─────────────────────────────────────────────────────────

export type ProfileSummary = {
  id: string
  title: string
  one_line_summary: string
  elements: ElementMap
  dominant_elements: string[]
  lacking_elements: string[]
  keywords: string[]
  chart_identity_summary?: ChartIdentitySummary
}

export type InsightSummary = {
  id: string
  semantic_key: string
  label: string
  type:
    | 'general_reading'
    | 'compatibility_result'
    | 'fortune_flow'
    | 'timing_recommendation'
  short_summary: string
}

export type HistoryItem = {
  id: string
  semantic_key: string
  template: ActiveTemplate
  title: string
  summary: string
  created_at: string
  updated_at: string
}

export type CounselingBoard = {
  profile_summary: ProfileSummary | null
  active_reading: ActiveReading | null
  insight_summaries: InsightSummary[]
  history: HistoryItem[]
}

// ─── UI Event ─────────────────────────────────────────────────────────────────

export type UIEvent =
  | { type: 'report_initialized'; target_id: string }
  | { type: 'tab_recommended'; recommended_tab: RecommendedTab }
  | { type: 'profile_initialized'; target_id: string }
  | { type: 'template_changed'; from_template: ActiveTemplate | null; to_template: ActiveTemplate; target_id: string }
  | { type: 'active_reading_updated'; target_id: string; changed_fields: string[] }
  | { type: 'insight_added'; target_id: string }
  | { type: 'reading_completed'; target_id: string }
  | { type: 'reading_updated'; target_id: string }
  | null

// ─── Agent Trace ──────────────────────────────────────────────────────────────

export type AgentTraceStep = {
  step: 'tool_call' | 'view_model' | 'graph_node' | 'routing' | 'llm_call' | string
  label: string
  tool_name?: string | null
  status: 'pending' | 'completed' | 'skipped' | 'failed'
}

export type PreludePayload = {
  session_id: string
  current_stage: CurrentStage
  recommended_tab: RecommendedTab
  partner_intake_requested: boolean
  saju_report: SajuReport
  counseling_board: CounselingBoard
  ui_event: UIEvent | null
  tool_agent_trace: AgentTraceStep[]
}

// ─── API Responses ────────────────────────────────────────────────────────────

export type InitialReadingResponse = {
  session_id: string
  assistant_message: string
  current_stage: 'initial_report'
  recommended_tab: 'saju_report'
  thinking_state: string | null
  saju_report: SajuReport
  counseling_board: CounselingBoard
  ui_event: UIEvent
  agent_trace?: AgentTraceStep[]
}

export type ChatResponse = {
  session_id: string
  assistant_message: string
  current_stage: CurrentStage
  recommended_tab: RecommendedTab
  thinking_state: string | null
  saju_report: SajuReport
  counseling_board: CounselingBoard
  ui_event: UIEvent
  agent_trace?: AgentTraceStep[]
  partner_intake_requested: boolean
}
