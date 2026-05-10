from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.saju import ElementName

FortuneDomain = Literal["love", "career", "money", "relationships", "health", "overall"]
TimingDomain = Literal["love", "career", "money", "relationships", "health", "general"]
FortunePeriod = Literal["today", "this_week", "this_month", "current_phase"]
ActionType = Literal[
    "confession",
    "job_change",
    "interview",
    "important_conversation",
    "investment_decision",
    "move",
    "start_something",
    "end_something",
    "other",
]
ReadingTone = Literal["muted", "soft", "highlight", "strong"]
ConnectionType = Literal["supportive", "balanced", "tense"]


class CompatibilityPersonSnapshot(BaseModel):
    name: str
    dominant_element: ElementName | None = None


class CompatibilityResult(BaseModel):
    semantic_key: str
    score: int = Field(ge=0, le=100)
    label: str
    people: list[CompatibilityPersonSnapshot]
    connection_type: ConnectionType
    connection_label: str
    strengths: list[str]
    friction_points: list[str]
    one_line_advice: str
    summary: str


class FortuneSegment(BaseModel):
    label: str
    keyword: str
    tone: ReadingTone | None = None


class DomainFortuneResult(BaseModel):
    semantic_key: str
    domain: FortuneDomain
    period: FortunePeriod
    headline_keyword: str
    one_line_summary: str
    segments: list[FortuneSegment]
    recommended_action: str | None = None
    score: int = Field(ge=0, le=100)
    flow_label: str
    summary: str


class TimingWindow(BaseModel):
    label: str
    date_range: str
    reason: str
    score: int | None = Field(default=None, ge=0, le=100)


class TimingResult(BaseModel):
    semantic_key: str
    domain: TimingDomain
    action_type: ActionType
    headline_keyword: str
    one_line_summary: str
    recommended_window: TimingWindow
    timeline: list[FortuneSegment] | None = None
    caution_window: TimingWindow | None = None
    timing_score: int = Field(ge=0, le=100)
    summary: str
