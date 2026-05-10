"""만세력·규칙 시그널을 한국어로 읽기 쉽게 묶은 스냅샷 (API·LLM 공용)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TraditionalChartDigest(BaseModel):
    """사주 풀이에 쓰는 전통 표기 요약 (한글 위주)."""

    pillars_hanja: dict[str, str] = Field(
        ...,
        description="year·month·day·(hour) → 한자 간지 문자열 (예: year=戊寅; 시 미입력 시 hour 키 생략)",
    )

    day_stem_oheng_ko: str = Field(..., description="일간 오행 한글 호칭, 예: 신금")
    ilju_ganji_hangul: str = Field(..., description="일주 간지 한글 음, 예: 신묘")
    ilju_branch_animal_ko: str = Field(..., description="일지 띠, 예: 토끼")
    pillar_lines_ko: list[str] = Field(
        ...,
        description="연·월·일·(시) 기둥 한 줄 요약 (한글)",
    )
    day_master_strength_ko: str = Field(
        default="",
        description="일간 강약 요약 (엔진 메트릭 기반, 한글)",
    )
    signals_ko: dict[str, list[str]] = Field(
        default_factory=dict,
        description="섹션별 규칙 엔진 시그널에 대한 한글 한줄 풀이",
    )
