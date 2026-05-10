from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[3]
MOCKS_DIR = REPO_ROOT / "docs" / "mocks"


@pytest.fixture()
def mocks_dir() -> Path:
    return MOCKS_DIR


def load_mock_json(filename: str) -> dict[str, Any]:
    path = MOCKS_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())
