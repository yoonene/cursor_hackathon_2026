"""초기 상담 NLG(LLM 출력) 스키마."""

from __future__ import annotations

from pydantic import BaseModel, Field


class InitialReadingLLMOutput(BaseModel):
    """LLM이 작성하는 첫 리딩 채널 메시지 + 대시보드용 요약 (템플릿 YAML 미사용)."""

    assistant_message: str = Field(
        ...,
        description="채팅에 들어가는 전체 영문 초기 해석 (상담사 톤).",
    )
    overall_summary: str
    keywords: list[str] = Field(min_length=3, max_length=5)
    personality: str
    relationship_style: str
    career_style: str
    emotional_pattern: str
    strengths: list[str] = Field(min_length=1, max_length=5)
    cautions: list[str] = Field(min_length=1, max_length=5)
    one_line_verdict: str
