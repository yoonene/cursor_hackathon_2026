from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

_LOG_FORMAT = "[%(asctime)s] [%(levelname)-5s] [%(name)-20s] %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# src/backend/logs/app.log
_LOG_DIR = Path(__file__).resolve().parents[2] / "logs"


def setup_logging(log_level: str = "INFO") -> None:
    """앱 로깅 초기화. main.py 시작 시 한 번 호출한다."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        _LOG_DIR / "app.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        root.addHandler(console_handler)
        root.addHandler(file_handler)

    # 외부 라이브러리 노이즈 억제
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("langgraph").setLevel(logging.WARNING)
