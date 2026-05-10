"""Lightweight birth-date extraction from free text (Ko + ISO)."""

from __future__ import annotations

import re
from calendar import monthrange
from datetime import date

_ISO = re.compile(r"\b(?P<y>\d{4})-(?P<m>\d{2})-(?P<d>\d{2})\b")
_DOT = re.compile(r"\b(?P<y>\d{4})\.(?P<m>\d{1,2})\.(?P<d>\d{1,2})\b")
_SLASH = re.compile(r"\b(?P<y>\d{4})/(?P<m>\d{1,2})/(?P<d>\d{1,2})\b")
_COMPACT = re.compile(r"\b(?P<y>\d{4})(?P<m>\d{2})(?P<d>\d{2})\b")
_KR_FULL = re.compile(
    r"(?P<y>\d{4})\s*년\s*(?P<m>\d{1,2})\s*월\s*(?P<d>\d{1,2})\s*일",
)


def _safe_date(year: int, month: int, day: int) -> date | None:
    try:
        if not (1 <= month <= 12):
            return None
        if not (1 <= day <= monthrange(year, month)[1]):
            return None
        return date(year, month, day)
    except ValueError:
        return None


def extract_birth_dates_from_text(text: str) -> list[date]:
    """Return plausible dates found in `text`, ordered left-to-right, deduped."""
    matches: list[tuple[int, date]] = []
    for matcher in (_ISO, _DOT, _SLASH, _KR_FULL, _COMPACT):
        for m in matcher.finditer(text):
            y, mo, d = int(m.group("y")), int(m.group("m")), int(m.group("d"))
            if matcher is _COMPACT and not (1850 <= y <= 2099):
                continue
            parsed = _safe_date(y, mo, d)
            if parsed:
                matches.append((m.start(), parsed))

    matches.sort(key=lambda md: md[0])
    seen: list[date] = []
    for _, parsed in matches:
        if parsed not in seen:
            seen.append(parsed)
    return seen


def extract_first_birth_date(text: str) -> date | None:
    dates = extract_birth_dates_from_text(text)
    return dates[0] if dates else None
