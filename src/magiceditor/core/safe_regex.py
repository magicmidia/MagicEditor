"""Bounded user regex compile (ReDoS guard)."""

from __future__ import annotations

import re
from re import Pattern

from magiceditor.core.text_match import PatternError, compile_pattern

MAX_PATTERN_LEN = 256
MAX_NESTED = 8


def compile_user_pattern(
    needle: str,
    *,
    case_sensitive: bool = False,
    use_regex: bool = False,
    max_len: int = MAX_PATTERN_LEN,
) -> Pattern[str]:
    """Compile a user find pattern with length / nesting caps."""
    if not needle:
        raise PatternError("empty pattern")
    if len(needle) > max_len:
        raise PatternError(f"pattern longer than {max_len} characters")
    if use_regex:
        if needle.count("(") > MAX_NESTED or needle.count("{") > MAX_NESTED:
            raise PatternError("pattern too nested")
        if re.search(r"(\.\*){3,}|(\+\+)|(\{\d{4,})", needle):
            raise PatternError("pattern too expensive")
    return compile_pattern(needle, case_sensitive=case_sensitive, use_regex=use_regex)
