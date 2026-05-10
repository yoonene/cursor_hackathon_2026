from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with CLod configuration kept visible and centralized."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Saju Counselor"
    environment: str = "development"
    default_timezone: str = "Asia/Seoul"
    """만세력 연월일시 로컬화에 사용할 IANA 타임존 (인테이크에 시간대 필드 없을 때)."""
    clod_api_key: str | None = None
    clod_base_url: str | None = None
    clod_fast_model: str | None = None
    clod_strong_model: str | None = None
    clod_creative_model: str | None = None
    log_level: str = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
