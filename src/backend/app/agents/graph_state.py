"""LangGraph 공유 상태 TypedDict.

각 에이전트 노드는 이 상태를 읽고 부분 업데이트 dict를 반환한다.
total=False: 모든 필드가 선택적 — 노드별 부분 업데이트가 가능하도록.
"""

from __future__ import annotations

from datetime import date, time
from typing import TYPE_CHECKING  # noqa: F401

from typing_extensions import TypedDict

from app.core.config import Settings
from app.schemas.fortune import CompatibilityResult, DomainFortuneResult, TimingResult
from app.schemas.intake import GenderType
from app.schemas.profiles import PersonProfile
from app.schemas.requests import PartnerCompatibilityPayload
from app.schemas.saju import SajuData
from app.schemas.state import ConversationState
from app.schemas.view_models import AgentTraceStep, UIEvent
from app.services.followup_intent_classifier import ClassifiedFollowUpIntent

if TYPE_CHECKING:
    pass


class AgentGraphState(TypedDict, total=False):
    # ── 입력 (chat_service → graph) ──────────────────────────
    settings: Settings
    conversation_state: ConversationState
    message: str
    structured_partner: PartnerCompatibilityPayload | None

    # ── 라우터 에이전트 출력 ──────────────────────────────────
    intent: ClassifiedFollowUpIntent | None
    next_node: str

    # 라우터가 파싱한 상대방 정보 → 사주 에이전트로 전달
    resolved_partner_birth: date | None
    resolved_partner_name: str | None
    resolved_partner_time: time | None
    resolved_partner_gender: GenderType | None

    # ── 사주 에이전트 출력 ────────────────────────────────────
    partner_profile: PersonProfile | None
    partner_saju: SajuData | None

    # ── 각 에이전트 도구 결과 ─────────────────────────────────
    compat_result: CompatibilityResult | None
    fortune_result: DomainFortuneResult | None
    timing_result: TimingResult | None

    # ── 최종 출력 (graph → chat_service) ─────────────────────
    supplemental_context: str | None
    ui_event: UIEvent | None
    partner_intake_requested: bool
    agent_traces: list[AgentTraceStep]
