"""규칙 엔진 시그널 코드 → 한국어 한줄 설명 (표시용)."""

from __future__ import annotations

SIGNAL_GLOSS_KO: dict[str, str] = {
    "initiative_high": "두드러진 추진력·먼저 나서는 패턴이 강합니다.",
    "growth_oriented": "방향 설정·학습·확장 쪽 에너지가 잘 깨어납니다.",
    "expressive_presence": "표현력·외연(밖으로 드러나는 존재감)이 분명합니다.",
    "analytical_focus_high": "분석·기준 정리가 빠르고 구조적으로 보려 합니다.",
    "emotional_sensitivity_high": "기류·무드 민감도가 높고 내부 처리가 깊을 수 있습니다.",
    "stability_high": "끝까지 버티거나 다지는 힘이 버팀목으로 작동합니다.",
    "leadership_fit": "목표 세우고 끌고 가는 책무에 기회가 많습니다.",
    "creative_fit": "새 형태 만들기·시도 에너지가 활용도가 높습니다.",
    "strategy_fit": "판을 읽고 타이밍 잡는 쪽 장점이 포착됩니다.",
    "operations_fit": "실행 절차 다듬고 굴리는 데 장점이 큽니다.",
    "people_oriented_fit": "사람·관계 속에서 결과를 내기 쉬운 패턴입니다.",
    "affection_direct": "호감·정이 직설적으로 전해지는 축입니다.",
    "emotional_depth_high": "연정 쪽 깊이·몰입이 손쉽게 열립니다.",
    "relationship_stability_seek": "관계에서는 안전·예측가능 리듬을 중시합니다.",
    "needs_personal_space": "호흡·거리 재조정이 번아웃 예방에 중요합니다.",
    "wealth_growth_potential": "자산이 불어날 여지와 방향 선택지가 많아 보입니다.",
    "wealth_planning_strength": "장부·설계처럼 맥락 잡아 절약/확충 균형이 좋습니다.",
    "wealth_opportunity_sense": "기회에 반응해 움직이는 감이 있습니다.",
    "stability_low": "기반이 들쭉날쭉할 때 감정/일정도 흔들리기 쉽습니다.",
    "burnout_risk": "한꺼번에 과부하 줄 때 회복까지 길어질 수 있습니다.",
    "overthinking_risk": "머리가 빙 돌며 결정 타이밍이 늦어질 수 있습니다.",
    "decision_scatter_risk": "선택지가 많을수록 초점 분산이 우려됩니다.",
    "relationship_guardedness": "마음을 덜 내줄 때 오해 거리가 쌓이기 쉽습니다.",
}


def gloss_signals_by_section(raw: dict[str, list[str]]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for section, codes in raw.items():
        lines: list[str] = []
        for code in codes:
            lines.append(SIGNAL_GLOSS_KO.get(code, f"{code}: 규칙 엔진에서 마킹된 신호입니다."))
        if lines:
            out[section] = lines
    return out
