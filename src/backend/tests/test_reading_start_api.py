from __future__ import annotations

import uuid

from app.schemas.responses import InitialReadingResponse

from tests.conftest import load_mock_json

MOCK_ELEMENT_KEYS = {"wood", "fire", "earth", "metal", "water"}


def test_health_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_post_reading_start_matches_schema(client):
    body = load_mock_json("00_start_reading_request.json")
    body = {**body, "session_id": f"test-session-{uuid.uuid4().hex[:12]}"}

    response = client.post("/reading/start", json=body)
    assert response.status_code == 200, response.text

    data = InitialReadingResponse.model_validate(response.json())
    assert data.current_stage == "initial_report"
    assert data.recommended_tab == "saju_report"
    assert data.ui_event is not None
    assert data.ui_event.type == "report_initialized"
    assert data.saju_report.elements.model_dump().keys() == {
        "wood",
        "fire",
        "earth",
        "metal",
        "water",
    }
    assert data.counseling_board.profile_summary is not None
    assert data.counseling_board.active_reading is None


def test_post_reading_start_rejects_missing_birth_date(client):
    response = client.post(
        "/reading/start",
        json={"session_id": "x", "display_name": "A"},
    )
    assert response.status_code == 422


def test_post_reading_start_aligns_demo_mock_contract_shape(client):
    """Mock `01` 계약 예시와 동일한 플래그·보드 초기 상태(오행 키, active_reading 비어 있음 등)인지 확인한다."""
    request_body = load_mock_json("00_start_reading_request.json")
    demo = load_mock_json("01_initial_reading_response.json")
    session_id = f"test-session-{uuid.uuid4().hex[:12]}"

    response = client.post(
        "/reading/start",
        json={**request_body, "session_id": session_id},
    )
    assert response.status_code == 200, response.text
    live = response.json()

    assert live["session_id"] == session_id
    assert live["current_stage"] == demo["current_stage"]
    assert live["recommended_tab"] == demo["recommended_tab"]
    assert live["counseling_board"]["active_reading"] == demo["counseling_board"]["active_reading"]
    assert set(live["saju_report"]["elements"]) == MOCK_ELEMENT_KEYS
    assert set(live["counseling_board"]["profile_summary"]["elements"]) == MOCK_ELEMENT_KEYS
    assert isinstance(live["assistant_message"], str) and len(live["assistant_message"]) > 0
