from __future__ import annotations

import socket
import sys
import time
import uuid
from collections.abc import Generator
from typing import Final

import httpx
import pytest

from app.schemas.responses import InitialReadingResponse

from tests.conftest import BACKEND_ROOT, load_mock_json

_HEALTH_PATH: Final = "/health"
_START_PATH: Final = "/reading/start"
_READY_TIMEOUT_SEC: Final = 20.0
_POLL_INTERVAL_SEC: Final = 0.15


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_until_ready(base_url: str) -> None:
    deadline = time.monotonic() + _READY_TIMEOUT_SEC
    last_err: str | None = None
    while time.monotonic() < deadline:
        try:
            response = httpx.get(f"{base_url}{_HEALTH_PATH}", timeout=1.0)
            if response.status_code == 200 and response.json().get("status") == "ok":
                return
        except OSError as exc:
            last_err = str(exc)
        except httpx.HTTPError as exc:
            last_err = str(exc)
        time.sleep(_POLL_INTERVAL_SEC)
    raise RuntimeError(
        f"Uvicorn did not become ready within {_READY_TIMEOUT_SEC}s"
        + (f": {last_err}" if last_err else "")
    )


@pytest.fixture(scope="session")
def live_base_url() -> Generator[str, None, None]:
    """실제 `uvicorn` 서브프로세스를 띄운 뒤 `http://127.0.0.1:{port}` 를 반환한다."""
    import os
    import subprocess

    port = _pick_free_port()
    base_url = f"http://127.0.0.1:{port}"

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=BACKEND_ROOT,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_until_ready(base_url)
        yield base_url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)


@pytest.mark.integration
def test_live_http_health(live_base_url: str) -> None:
    response = httpx.get(f"{live_base_url}{_HEALTH_PATH}", timeout=5.0)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.integration
def test_live_http_reading_start_from_mock_request(live_base_url: str) -> None:
    body = load_mock_json("00_start_reading_request.json")
    body = {**body, "session_id": f"live-http-{uuid.uuid4().hex[:12]}"}

    response = httpx.post(
        f"{live_base_url}{_START_PATH}",
        json=body,
        headers={"Content-Type": "application/json"},
        timeout=15.0,
    )
    assert response.status_code == 200, response.text

    data = InitialReadingResponse.model_validate(response.json())
    assert data.current_stage == "initial_report"
    assert data.recommended_tab == "saju_report"
    assert data.counseling_board.profile_summary is not None
    assert data.counseling_board.active_reading is None
