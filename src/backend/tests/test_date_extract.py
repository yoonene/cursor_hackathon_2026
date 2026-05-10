"""Birth-date extraction helpers."""

from __future__ import annotations

from datetime import date

from app.services.date_extract import extract_birth_dates_from_text, extract_first_birth_date


def test_extract_iso_first() -> None:
    assert extract_first_birth_date("Partner 1992-05-20") == date(1992, 5, 20)


def test_extract_korean_date() -> None:
    assert extract_first_birth_date("상대방 1999년 7월 7일생") == date(1999, 7, 7)


def test_extract_multiple_keeps_order() -> None:
    dates = extract_birth_dates_from_text("나 1990-01-01 그리고 2000년 12월 12일")
    assert dates == [date(1990, 1, 1), date(2000, 12, 12)]


def test_extract_dotted_slash_compact() -> None:
    assert extract_first_birth_date("상대 생일은 1992.05.20") == date(1992, 5, 20)
    assert extract_first_birth_date("연도 1988/1/09") == date(1988, 1, 9)
    assert extract_first_birth_date("번호 19940913 문자") == date(1994, 9, 13)
