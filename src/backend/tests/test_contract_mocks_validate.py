from __future__ import annotations

import pytest

from app.schemas.intake import StartReadingRequest
from app.schemas.responses import ChatResponse, InitialReadingResponse

from tests.conftest import MOCKS_DIR, load_mock_json

INITIAL_FILES = ("01_initial_reading_response.json",)

CHAT_FILES = (
    "02_counseling_start_general_reading.json",
    "03_compatibility_pending.json",
    "04_compatibility_result.json",
    "05_timing_recommendation_love.json",
    "06_fortune_flow_career_week.json",
    "07_timing_recommendation_career.json",
)


@pytest.mark.parametrize("filename", INITIAL_FILES)
def test_initial_reading_mocks_validate(filename: str) -> None:
    payload = load_mock_json(filename)
    validated = InitialReadingResponse.model_validate(payload)
    assert validated.session_id


@pytest.mark.parametrize("filename", CHAT_FILES)
def test_chat_response_mocks_validate(filename: str) -> None:
    payload = load_mock_json(filename)
    validated = ChatResponse.model_validate(payload)
    assert validated.session_id
    assert validated.counseling_board is not None


def test_mock_request_fixture_parses() -> None:
    payload = load_mock_json("00_start_reading_request.json")
    req = StartReadingRequest.model_validate(payload)
    assert req.session_id == "demo-session-001"
    assert str(req.birth_date) == "1998-04-21"


def test_mocks_directory_exists_and_lists_contract_files() -> None:
    assert MOCKS_DIR.is_dir()
    names = {p.name for p in MOCKS_DIR.glob("*.json")}
    expected = {
        "00_start_reading_request.json",
        *INITIAL_FILES,
        *CHAT_FILES,
    }
    assert expected <= names
