"""Text matching helpers (literal or regex) — Qt-free."""

from __future__ import annotations

import re
from re import Pattern


class PatternError(ValueError):
    """Invalid regular expression."""


def compile_pattern(
    needle: str,
    *,
    case_sensitive: bool = False,
    use_regex: bool = False,
) -> Pattern[str]:
    """Compile a search pattern. Raises ``PatternError`` on bad regex."""
    if not needle:
        raise PatternError("empty pattern")
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        if use_regex:
            return re.compile(needle, flags)
        return re.compile(re.escape(needle), flags)
    except re.error as exc:
        raise PatternError(str(exc)) from exc


def find_first(
    text: str,
    pattern: Pattern[str],
    *,
    start: int = 0,
    end: int | None = None,
) -> re.Match[str] | None:
    """First match at or after ``start`` (optionally before ``end``)."""
    if end is None:
        return pattern.search(text, start)
    return pattern.search(text, start, end)


def find_last_before(
    text: str,
    pattern: Pattern[str],
    *,
    before: int,
) -> re.Match[str] | None:
    """Last match that starts strictly before ``before`` (or any if before==0 for wrap)."""
    last: re.Match[str] | None = None
    for m in pattern.finditer(text):
        if m.start() < before:
            last = m
        else:
            break
    return last


def find_all_matches(text: str, pattern: Pattern[str]) -> list[re.Match[str]]:
    return list(pattern.finditer(text))


def expand_replacement(match: re.Match[str], template: str) -> str:
    """Expand ``\\1`` / ``\\g<name>`` groups; plain string if no backrefs needed."""
    try:
        return match.expand(template)
    except (re.error, IndexError):
        return template
