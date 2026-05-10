"""Map deterministic tool outputs onto `CounselingBoard` + readable JSON for the counselor LLM."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from app.schemas.fortune import CompatibilityResult, DomainFortuneResult, FortuneDomain, FortunePeriod, TimingResult
from app.schemas.view_models import (
    CounselingBoard,
    CompatibilityConnection,
    CompatibilityPendingPerson,
    CompatibilityPendingTemplate,
    CompatibilityResultPerson,
    CompatibilityResultTemplate,
    FortuneFlowTemplate,
    HistoryItem,
    InsightSummary,
    TimelineSegment,
    TimingRecommendationTemplate,
    TimingWindowView,
)


def _utc_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _slug_suffix(key: str) -> str:
    out = []
    for ch in key.replace(":", "_").replace("/", "_"):
        if ch.isalnum() or ch == "_":
            out.append(ch)
        else:
            out.append("_")
    s = "".join(out).strip("_")
    return (s[:96] or "reading").lower()


def fortune_flow_title(domain: FortuneDomain, period: FortunePeriod) -> str:
    period_label = {
        "today": "Today",
        "this_week": "This Week",
        "this_month": "This Month",
        "current_phase": "Current Phase",
    }[period]
    domain_label = domain.replace("_", " ").title()
    return f"{period_label}'s {domain_label} Flow"


def timing_view_title(domain: str, action_type: str) -> str:
    return {
        ("love", "confession"): "Best Time to Confess",
        ("career", "interview"): "Interview Timing",
        ("career", "job_change"): "Career Move Timing",
        ("money", "investment_decision"): "Investment Timing",
        ("relationships", "important_conversation"): "Sensitive Conversation Timing",
        ("general", "move"): "Moving Timing",
        ("general", "start_something"): "Starting Something New",
        ("general", "end_something"): "Closing a Chapter",
    }.get((domain, action_type), "Recommended Timing Window")


def upsert_insight_summaries(summaries: list[InsightSummary], item: InsightSummary) -> None:
    for idx, existing in enumerate(summaries):
        if existing.semantic_key == item.semantic_key:
            summaries[idx] = item
            return
    summaries.insert(0, item)


def upsert_history_items(history: list[HistoryItem], item: HistoryItem) -> None:
    for idx, existing in enumerate(history):
        if existing.semantic_key == item.semantic_key:
            history[idx] = item
            return
    history.insert(0, item)


def attach_domain_fortune(board: CounselingBoard, result: DomainFortuneResult) -> tuple[str, str]:
    """Mutates `board.active_reading`, insights, history. Returns (reading_id, llm_context_json)."""

    rid = "fortune_flow_" + _slug_suffix(result.semantic_key)
    tmpl = FortuneFlowTemplate(
        id=rid,
        semantic_key=result.semantic_key,
        template="fortune_flow",
        title=fortune_flow_title(result.domain, result.period),
        domain=result.domain,
        period=result.period,
        headline_keyword=result.headline_keyword,
        one_line_summary=result.one_line_summary,
        segments=[
            TimelineSegment(label=s.label, keyword=s.keyword, tone=s.tone) for s in result.segments
        ],
        recommended_action=result.recommended_action,
    )
    now = _utc_z()
    label = f"{result.domain.replace('_', ' ')} rhythm ({result.period.replace('_', ' ')})"
    insight = InsightSummary(
        id=f"insight_{rid}",
        semantic_key=result.semantic_key,
        label=label,
        type="fortune_flow",
        short_summary=f"{result.headline_keyword} — score ~{result.score}",
    )
    hist = HistoryItem(
        id=f"history_{rid}",
        semantic_key=result.semantic_key,
        template="fortune_flow",
        title=tmpl.title,
        summary=result.summary[:480],
        created_at=now,
        updated_at=now,
    )
    board.active_reading = tmpl
    upsert_insight_summaries(board.insight_summaries, insight)
    upsert_history_items(board.history, hist)

    payload = {
        "tool": "analyze_domain_fortune",
        "semantic_key": result.semantic_key,
        "domain": result.domain,
        "period": result.period,
        "score": result.score,
        "flow_label": result.flow_label,
        "headline_keyword": result.headline_keyword,
        "one_line_summary": result.one_line_summary,
        "recommended_action": result.recommended_action,
        "segments": [{"label": s.label, "keyword": s.keyword, "tone": s.tone} for s in result.segments],
    }
    return rid, json.dumps(payload, ensure_ascii=False)


def attach_timing(board: CounselingBoard, result: TimingResult) -> tuple[str, str]:
    rid = "timing_" + _slug_suffix(result.semantic_key)
    timeline = (
        [TimelineSegment(label=s.label, keyword=s.keyword, tone=s.tone) for s in result.timeline]
        if result.timeline
        else None
    )
    cw = result.caution_window
    caution_view = (
        TimingWindowView(label=cw.label, date_range=cw.date_range, reason=cw.reason) if cw else None
    )
    rw = result.recommended_window
    tmpl = TimingRecommendationTemplate(
        id=rid,
        semantic_key=result.semantic_key,
        template="timing_recommendation",
        title=timing_view_title(result.domain, result.action_type),
        domain=result.domain,
        action_type=result.action_type,
        headline_keyword=result.headline_keyword,
        one_line_summary=result.one_line_summary,
        recommended_window=TimingWindowView(
            label=rw.label,
            date_range=rw.date_range,
            reason=rw.reason,
        ),
        timeline=timeline,
        caution_window=caution_view,
    )
    now = _utc_z()
    insight = InsightSummary(
        id=f"insight_{rid}",
        semantic_key=result.semantic_key,
        label="Timing window",
        type="timing_recommendation",
        short_summary=f"{rw.date_range} (score ~{result.timing_score})",
    )
    hist = HistoryItem(
        id=f"history_{rid}",
        semantic_key=result.semantic_key,
        template="timing_recommendation",
        title=tmpl.title,
        summary=result.summary[:480],
        created_at=now,
        updated_at=now,
    )
    board.active_reading = tmpl
    upsert_insight_summaries(board.insight_summaries, insight)
    upsert_history_items(board.history, hist)

    payload = {
        "tool": "analyze_favorable_timing",
        "semantic_key": result.semantic_key,
        "domain": result.domain,
        "action_type": result.action_type,
        "timing_score": result.timing_score,
        "recommended_window": {"label": rw.label, "date_range": rw.date_range, "reason": rw.reason},
        "caution_window": (
            {"label": cw.label, "date_range": cw.date_range, "reason": cw.reason} if cw else None
        ),
        "one_line_summary": result.one_line_summary,
    }
    return rid, json.dumps(payload, ensure_ascii=False)


def attach_compatibility_pending(board: CounselingBoard, user_display: str | None) -> tuple[str, str]:
    rid = "compat_pending_partner"
    key = "compatibility:user:partner_pending"
    left = user_display or "You"
    tmpl = CompatibilityPendingTemplate(
        id=rid,
        semantic_key=key,
        template="compatibility_pending",
        title="Reading the connection",
        left_person=CompatibilityPendingPerson(name=left),
        right_person=None,
        status_message="Share your partner's birth date (YYYY-MM-DD or yyyy년 m월 d일) when you can.",
        missing_fields=["counterpart_birth_date"],
    )
    board.active_reading = tmpl
    return rid, json.dumps(
        {
            "tool": "compatibility_pending",
            "semantic_key": key,
            "instructions": "Collect partner birth date before running analyze_compatibility.",
        },
        ensure_ascii=False,
    )


def attach_compatibility_result(board: CounselingBoard, result: CompatibilityResult) -> tuple[str, str]:
    rid = "compatibility_" + _slug_suffix(result.semantic_key)
    tmpl = CompatibilityResultTemplate(
        id=rid,
        semantic_key=result.semantic_key,
        template="compatibility_result",
        title=f"Relationship Flow with {result.people[1].name}",
        score=result.score,
        label=result.label,
        people=[
            CompatibilityResultPerson(name=p.name, dominant_element=p.dominant_element)
            for p in result.people
        ],
        connection=CompatibilityConnection(type=result.connection_type, label=result.connection_label),
        strengths=list(result.strengths),
        friction_points=list(result.friction_points),
        one_line_advice=result.one_line_advice,
    )
    now = _utc_z()
    other = result.people[1].name
    insight = InsightSummary(
        id=f"insight_{rid}",
        semantic_key=result.semantic_key,
        label=f"Pull with {other}",
        type="compatibility_result",
        short_summary=f"{result.score} pts — {result.connection_label}",
    )
    hist = HistoryItem(
        id=f"history_{rid}",
        semantic_key=result.semantic_key,
        template="compatibility_result",
        title=tmpl.title,
        summary=result.summary[:480],
        created_at=now,
        updated_at=now,
    )
    board.active_reading = tmpl
    upsert_insight_summaries(board.insight_summaries, insight)
    upsert_history_items(board.history, hist)

    payload = {
        "tool": "analyze_compatibility",
        "semantic_key": result.semantic_key,
        "score": result.score,
        "label": result.label,
        "connection_type": result.connection_type,
        "people": [{"name": p.name, "dominant_element": p.dominant_element} for p in result.people],
        "strengths": result.strengths,
        "friction_points": result.friction_points,
        "one_line_advice": result.one_line_advice,
    }
    return rid, json.dumps(payload, ensure_ascii=False)
