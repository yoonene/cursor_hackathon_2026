"""SSE `POST /chat/stream` smoke tests (stubbed streamed LLM to avoid outbound calls)."""

from __future__ import annotations

import json
import uuid

import pytest

from app.services import chat_service


@pytest.fixture(autouse=True)
def _disable_followup_llm_router(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.followup_intent_classifier._llm_classify",
        lambda *args, **kwargs: None,
    )


@pytest.fixture(autouse=True)
def _stub_stream_follow(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_stream(settings, state, supplemental_context=None):  # noqa: ARG001
        yield "delta", "stub"
        yield "end", "llm_ok"

    monkeypatch.setattr(
        chat_service,
        "stream_follow_up_counselor_text",
        fake_stream,
    )


def test_chat_stream_emits_prelude_delta_complete(client):
    sid = str(uuid.uuid4())
    start = client.post(
        "/reading/start",
        json={
            "session_id": sid,
            "birth_date": "1998-04-21",
            "birth_time": "14:30",
            "gender": "female",
        },
    )
    assert start.status_code == 200

    prelude = delta = complete = None
    with client.stream(
        "POST",
        "/chat/stream",
        json={"session_id": sid, "message": "금전운 어때"},
    ) as resp:
        assert resp.status_code == 200
        current = ""
        for line in resp.iter_lines():
            if not line:
                continue
            if line.startswith("event:"):
                current = line[len("event:") :].strip()
            elif line.startswith("data:"):
                blob = json.loads(line[len("data:") :].strip())
                if current == "prelude":
                    prelude = blob
                elif current == "delta":
                    delta = blob
                elif current == "complete":
                    complete = blob

    assert prelude is not None and prelude["session_id"] == sid
    assert prelude["counseling_board"]["active_reading"]["template"] == "fortune_flow"
    assert delta == {"text": "stub"}
    assert complete is not None
    assert complete["assistant_message"] == "stub"
    assert complete["thinking_state"] is None


def test_chat_stream_unknown_session_404(client):
    with client.stream(
        "POST",
        "/chat/stream",
        json={"session_id": str(uuid.uuid4()), "message": "hi"},
    ) as resp:
        assert resp.status_code == 404


def test_chat_stream_prelude_partner_intake_flag_compat_pending(client):
    sid = str(uuid.uuid4())
    client.post("/reading/start", json={"session_id": sid, "birth_date": "1998-04-21", "gender": "female"})
    client.post("/chat", json={"session_id": sid, "message": "궁합 볼래"})

    prelude = None
    with client.stream(
        "POST",
        "/chat/stream",
        json={"session_id": sid, "message": "아직 안 넣었어"},
    ) as resp:
        assert resp.status_code == 200
        current = ""
        for line in resp.iter_lines():
            if not line:
                continue
            if line.startswith("event:"):
                current = line[len("event:") :].strip()
            elif line.startswith("data:") and current == "prelude":
                prelude = json.loads(line[len("data:") :].strip())

    assert prelude is not None
    assert prelude["current_stage"] == "collecting_compatibility_info"
    assert prelude["partner_intake_requested"] is True


def test_chat_api_bad_date_keeps_partner_intake_flag(client):
    sid = str(uuid.uuid4())
    client.post("/reading/start", json={"session_id": sid, "birth_date": "1998-04-21", "gender": "female"})
    client.post("/chat", json={"session_id": sid, "message": "궁합 볼래"})
    r = client.post("/chat", json={"session_id": sid, "message": "내일 우리 카페에서"})
    assert r.status_code == 200
    d = r.json()
    assert d["partner_intake_requested"] is True
