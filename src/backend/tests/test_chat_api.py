"""POST /chat: 세션 필요, 의도 라우팅 후 보드 반영 + 상담문."""

from __future__ import annotations

import uuid

import pytest

from app.services import chat_service
from app.services.session_store import session_store


@pytest.fixture(autouse=True)
def _stub_followup_counselor_reply(monkeypatch: pytest.MonkeyPatch) -> None:
    """환경에 API 키가 있어도 네트워크 없이 픽스처 테스트가 끝나도록 스텁."""

    monkeypatch.setattr(
        chat_service,
        "generate_followup_counseling_reply",
        lambda *args, **kwargs: ("(stub counsel)", "llm_ok"),
    )


@pytest.fixture(autouse=True)
def _disable_followup_llm_router(monkeypatch: pytest.MonkeyPatch) -> None:
    """테스트에서는 LLM 의도 분류를 끄고 규칙 기반 라우팅만 쓴다 (환경·네트워크 무관)."""
    monkeypatch.setattr(
        "app.services.followup_intent_classifier._llm_classify",
        lambda *args, **kwargs: None,
    )


def test_chat_unknown_session_returns_404(client):
    r = client.post("/chat", json={"session_id": str(uuid.uuid4()), "message": "안녕하세요"})
    assert r.status_code == 404


def test_chat_after_start_runs_domain_fortune_when_career_ask(client):
    sid = str(uuid.uuid4())
    payload = {
        "session_id": sid,
        "display_name": "테스트",
        "birth_date": "1998-04-21",
        "birth_time": "14:30",
        "gender": "female",
    }
    sr = client.post("/reading/start", json=payload)
    assert sr.status_code == 200

    cr = client.post("/chat", json={"session_id": sid, "message": "직업운이 궁금해요"})
    assert cr.status_code == 200
    data = cr.json()
    assert data["session_id"] == sid
    assert data["counseling_board"]["active_reading"]["template"] == "fortune_flow"
    assert data["counseling_board"]["active_reading"]["domain"] == "career"
    assert data["counseling_board"]["insight_summaries"]
    assert data["counseling_board"]["history"]
    assert data["ui_event"]["type"] == "template_changed"
    assert data["current_stage"] == "open_counseling"


def test_chat_money_domain_fortune(client):
    sid = str(uuid.uuid4())
    start = client.post(
        "/reading/start",
        json={
            "session_id": sid,
            "birth_date": "1990-01-15",
            "birth_time": "10:00",
            "gender": "male",
        },
    )
    assert start.status_code == 200
    cr = client.post("/chat", json={"session_id": sid, "message": "금전운 어때"})
    assert cr.status_code == 200
    ar = cr.json()["counseling_board"]["active_reading"]
    assert ar["template"] == "fortune_flow"
    assert ar["domain"] == "money"


def test_chat_timing_recommendation(client):
    sid = str(uuid.uuid4())
    start = client.post(
        "/reading/start",
        json={"session_id": sid, "birth_date": "1992-06-06", "birth_time": "09:30", "gender": "female"},
    )
    assert start.status_code == 200
    cr = client.post("/chat", json={"session_id": sid, "message": "언제 고백하면 좋아?"})
    assert cr.status_code == 200
    ar = cr.json()["counseling_board"]["active_reading"]
    assert ar["template"] == "timing_recommendation"
    assert ar["domain"] == "love"


def test_compat_routes_romance_fit_without_saying_gungap(client):
    sid = str(uuid.uuid4())
    start = client.post(
        "/reading/start",
        json={"session_id": sid, "birth_date": "1998-04-21", "gender": "female"},
    )
    assert start.status_code == 200
    cr = client.post(
        "/chat",
        json={
            "session_id": sid,
            "message": "썸 타는 사람이 있는데 이 사람이랑 잘 맞는지 궁금해",
        },
    )
    assert cr.status_code == 200
    d = cr.json()
    assert d["current_stage"] == "collecting_compatibility_info"
    assert d["counseling_board"]["active_reading"]["template"] == "compatibility_pending"


def test_chat_compatibility_when_birth_inline(client):
    sid = str(uuid.uuid4())
    start = client.post(
        "/reading/start",
        json={"session_id": sid, "birth_date": "1998-04-21", "gender": "female"},
    )
    assert start.status_code == 200
    cr = client.post(
        "/chat",
        json={"session_id": sid, "message": "우리 궁합 알려줘 상대방은 1992-05-20"},
    )
    assert cr.status_code == 200
    body = cr.json()
    assert body["counseling_board"]["active_reading"]["template"] == "compatibility_result"
    assert body["counseling_board"]["active_reading"]["score"] >= 0


def test_chat_compatibility_pending_then_partner_date(client):
    sid = str(uuid.uuid4())
    start = client.post(
        "/reading/start",
        json={
            "session_id": sid,
            "display_name": "민지",
            "birth_date": "1998-04-21",
            "birth_time": "14:30",
            "gender": "female",
        },
    )
    assert start.status_code == 200

    r1 = client.post("/chat", json={"session_id": sid, "message": "궁합 볼래"})
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["current_stage"] == "collecting_compatibility_info"
    assert d1["counseling_board"]["active_reading"]["template"] == "compatibility_pending"

    r2 = client.post("/chat", json={"session_id": sid, "message": "1995-06-02"})
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["current_stage"] == "open_counseling"
    assert d2["counseling_board"]["active_reading"]["template"] == "compatibility_result"


def test_compat_collection_partner_payload_without_message(client):
    sid = str(uuid.uuid4())
    start = client.post(
        "/reading/start",
        json={
            "session_id": sid,
            "display_name": "민지",
            "birth_date": "1998-04-21",
            "birth_time": "14:30",
            "gender": "female",
        },
    )
    assert start.status_code == 200
    client.post("/chat", json={"session_id": sid, "message": "궁합 볼래"})
    r = client.post(
        "/chat",
        json={
            "session_id": sid,
            "message": "",
            "partner": {
                "birth_date": "1994-03-03",
                "display_name": "테스트상대",
                "birth_time": "08:30",
                "gender": "male",
            },
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["current_stage"] == "open_counseling"
    assert body["counseling_board"]["active_reading"]["template"] == "compatibility_result"


def test_compat_state_repair_after_drift_partner_date_text(client):
    sid = str(uuid.uuid4())
    start = client.post(
        "/reading/start",
        json={
            "session_id": sid,
            "display_name": "민지",
            "birth_date": "1998-04-21",
            "birth_time": "14:30",
            "gender": "female",
        },
    )
    assert start.status_code == 200
    client.post("/chat", json={"session_id": sid, "message": "궁합 볼래"})

    corrupted = session_store.get(sid)
    assert corrupted is not None
    bad = corrupted.model_copy(deep=True)
    bad.current_stage = "open_counseling"
    bad.pending_tool_call = None
    session_store.set(bad)

    r = client.post("/chat", json={"session_id": sid, "message": "1995-06-02"})
    assert r.status_code == 200
    body = r.json()
    assert body["current_stage"] == "open_counseling"
    assert body["counseling_board"]["active_reading"]["template"] == "compatibility_result"


def test_compat_popup_refresh_sets_partner_intake_flag(client):
    sid = str(uuid.uuid4())
    start = client.post("/reading/start", json={"session_id": sid, "birth_date": "1998-04-21", "gender": "female"})
    assert start.status_code == 200
    client.post("/chat", json={"session_id": sid, "message": "궁합 볼래"})
    r = client.post("/chat", json={"session_id": sid, "message": "다시 입력하게 팝업 띄워줘"})
    assert r.status_code == 200
    d = r.json()
    assert d["partner_intake_requested"] is True
    assert d["counseling_board"]["active_reading"]["template"] == "compatibility_pending"


def test_compat_pending_response_includes_partner_intake_flag(client):
    sid = str(uuid.uuid4())
    start = client.post(
        "/reading/start",
        json={"session_id": sid, "birth_date": "1998-04-21", "gender": "female"},
    )
    assert start.status_code == 200
    r = client.post(
        "/chat",
        json={"session_id": sid, "message": "썸 타는 사람이 있는데 이 사람이랑 잘 맞는지 궁금해"},
    )
    assert r.status_code == 200
    assert r.json()["partner_intake_requested"] is True


def test_partner_payload_primes_even_if_pending_was_cleared(client):
    sid = str(uuid.uuid4())
    start = client.post("/reading/start", json={"session_id": sid, "birth_date": "1998-04-21", "gender": "female"})
    assert start.status_code == 200
    client.post("/chat", json={"session_id": sid, "message": "궁합 볼래"})

    corrupted = session_store.get(sid)
    assert corrupted is not None
    broken = corrupted.model_copy(deep=True)
    broken.pending_tool_call = None
    broken.current_stage = "open_counseling"
    session_store.set(broken)

    r = client.post(
        "/chat",
        json={"session_id": sid, "message": "", "partner": {"birth_date": "1993-08-08"}},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["counseling_board"]["active_reading"]["template"] == "compatibility_result"
    assert body["current_stage"] == "open_counseling"
