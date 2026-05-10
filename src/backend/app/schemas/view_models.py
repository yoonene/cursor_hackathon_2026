from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.schemas.fortune import FortuneDomain, FortunePeriod, ReadingTone
from app.schemas.saju import ElementBalance, ElementName

RecommendedTab = Literal["saju_report", "counseling_board"]
ActiveTemplate = Literal[
    "general_reading",
    "compatibility_pending",
    "compatibility_result",
    "fortune_flow",
    "timing_recommendation",
]


class ProfileSummary(BaseModel):
    id: str
    title: str
    one_line_summary: str
    elements: ElementBalance
    dominant_elements: list[ElementName]
    lacking_elements: list[ElementName]
    keywords: list[str]


class GeneralReadingTemplate(BaseModel):
    id: str
    semantic_key: str
    template: Literal["general_reading"]
    title: str
    headline: str | None = None
    body: str
    highlighted_traits: list[str] | None = None
    prompt_to_user: str | None = None


class CompatibilityPendingPerson(BaseModel):
    name: str | None = None


class CompatibilityPendingTemplate(BaseModel):
    id: str
    semantic_key: str
    template: Literal["compatibility_pending"]
    title: str
    left_person: CompatibilityPendingPerson
    right_person: CompatibilityPendingPerson | None = None
    status_message: str
    missing_fields: list[str] | None = None


class CompatibilityResultPerson(BaseModel):
    name: str
    dominant_element: ElementName | None = None


class CompatibilityConnection(BaseModel):
    type: Literal["supportive", "balanced", "tense"]
    label: str


class CompatibilityResultTemplate(BaseModel):
    id: str
    semantic_key: str
    template: Literal["compatibility_result"]
    title: str
    score: int = Field(ge=0, le=100)
    label: str
    people: list[CompatibilityResultPerson]
    connection: CompatibilityConnection
    strengths: list[str]
    friction_points: list[str]
    one_line_advice: str


class TimelineSegment(BaseModel):
    label: str
    keyword: str
    tone: ReadingTone | None = None


class FortuneFlowTemplate(BaseModel):
    id: str
    semantic_key: str
    template: Literal["fortune_flow"]
    title: str
    domain: FortuneDomain
    period: FortunePeriod
    headline_keyword: str
    one_line_summary: str
    segments: list[TimelineSegment]
    recommended_action: str | None = None


class TimingWindowView(BaseModel):
    label: str
    date_range: str
    reason: str


class TimingRecommendationTemplate(BaseModel):
    id: str
    semantic_key: str
    template: Literal["timing_recommendation"]
    title: str
    domain: Literal["love", "career", "money", "relationships", "health", "general"]
    action_type: str
    headline_keyword: str
    one_line_summary: str
    recommended_window: TimingWindowView
    timeline: list[TimelineSegment] | None = None
    caution_window: TimingWindowView | None = None


ActiveReading = Annotated[
    GeneralReadingTemplate
    | CompatibilityPendingTemplate
    | CompatibilityResultTemplate
    | FortuneFlowTemplate
    | TimingRecommendationTemplate,
    Field(discriminator="template"),
]


class InsightSummary(BaseModel):
    id: str
    semantic_key: str
    label: str
    type: Literal[
        "general_reading",
        "compatibility_result",
        "fortune_flow",
        "timing_recommendation",
    ]
    short_summary: str


class HistoryItem(BaseModel):
    id: str
    semantic_key: str
    template: ActiveTemplate
    title: str
    summary: str
    created_at: str
    updated_at: str


class CounselingBoard(BaseModel):
    profile_summary: ProfileSummary | None = None
    active_reading: ActiveReading | None = None
    insight_summaries: list[InsightSummary] = Field(default_factory=list)
    history: list[HistoryItem] = Field(default_factory=list)


class ReportInitializedEvent(BaseModel):
    type: Literal["report_initialized"]
    target_id: str


class TabRecommendedEvent(BaseModel):
    type: Literal["tab_recommended"]
    recommended_tab: RecommendedTab


class ProfileInitializedEvent(BaseModel):
    type: Literal["profile_initialized"]
    target_id: str


class TemplateChangedEvent(BaseModel):
    type: Literal["template_changed"]
    from_template: ActiveTemplate | None = None
    to_template: ActiveTemplate
    target_id: str


class ActiveReadingUpdatedEvent(BaseModel):
    type: Literal["active_reading_updated"]
    target_id: str
    changed_fields: list[str]


class InsightAddedEvent(BaseModel):
    type: Literal["insight_added"]
    target_id: str


class ReadingCompletedEvent(BaseModel):
    type: Literal["reading_completed"]
    target_id: str


class ReadingUpdatedEvent(BaseModel):
    type: Literal["reading_updated"]
    target_id: str


UIEvent = Annotated[
    ReportInitializedEvent
    | TabRecommendedEvent
    | ProfileInitializedEvent
    | TemplateChangedEvent
    | ActiveReadingUpdatedEvent
    | InsightAddedEvent
    | ReadingCompletedEvent
    | ReadingUpdatedEvent,
    Field(discriminator="type"),
]


class AgentTraceStep(BaseModel):
    step: Literal["tool_call", "view_model", "graph_node", "routing", "llm_call"]
    label: str
    tool_name: str | None = None
    status: Literal["pending", "completed", "skipped", "failed"] = "completed"
