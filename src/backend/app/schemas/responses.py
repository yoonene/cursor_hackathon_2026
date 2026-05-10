from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from app.schemas.report import SajuReport
from app.schemas.state import CurrentStage
from app.schemas.view_models import AgentTraceStep, CounselingBoard, RecommendedTab, UIEvent


class InitialReadingResponse(BaseModel):
    session_id: str
    assistant_message: str
    current_stage: Literal["initial_report"]
    recommended_tab: Literal["saju_report"]
    thinking_state: str | None
    saju_report: SajuReport
    counseling_board: CounselingBoard
    ui_event: UIEvent | None
    agent_trace: list[AgentTraceStep] | None = None


class ChatResponse(BaseModel):
    session_id: str
    assistant_message: str
    current_stage: CurrentStage
    recommended_tab: RecommendedTab
    thinking_state: str | None
    saju_report: SajuReport
    counseling_board: CounselingBoard
    ui_event: UIEvent | None
    agent_trace: list[AgentTraceStep] | None = None
    partner_intake_requested: bool = False


class ResetSessionResponse(BaseModel):
    session_id: str
    reset: bool


class HealthResponse(BaseModel):
    status: Literal["ok"]
