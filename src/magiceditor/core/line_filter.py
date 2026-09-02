"""Streaming line filter (P1) — extract matching lines without full text.

Pure core: no Qt. ``make_matcher`` builds a line predicate (literal
substring or safe user regex); ``filter_lines`` streams ``(line_number,
text)`` pairs over any iterable of lines and stops at ``max_matches``.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator

from magiceditor.core.safe_regex import MAX_PATTERN_LEN, compile_user_pattern
from magiceditor.core.text_match import PatternError

# Cap on extracted matches so a runaway pattern on a huge file cannot
# produce an unbounded result buffer.
DEFAULT_MAX_MATCHES = 1_000_000


def make_matcher(
    pattern: str,
    *,
    case_sensitive: bool,
    use_regex: bool,
    invert: bool = False,
) -> Callable[[str], bool]:
    """Build a line predicate. Raises ``PatternError`` on bad input."""
    if not pattern:
        raise PatternError("empty pattern")
    if len(pattern) > MAX_PATTERN_LEN:
        raise PatternError(f"pattern longer than {MAX_PATTERN_LEN} characters")
    if use_regex:
        rx = compile_user_pattern(pattern, case_sensitive=case_sensitive, use_regex=True)
        search = rx.search

        def matches(line: str) -> bool:
            return search(line) is not None

    elif case_sensitive:
        needle = pattern

        def matches(line: str) -> bool:
            return needle in line

    else:
        folded = pattern.casefold()

        def matches(line: str) -> bool:
            return folded in line.casefold()

    if not invert:
        return matches
    return lambda line: not matches(line)


def filter_lines(
    lines: Iterable[str],
    matcher: Callable[[str], bool],
    *,
    max_matches: int = DEFAULT_MAX_MATCHES,
) -> Iterator[tuple[int, str]]:
    """Yield ``(line_number_1based, text)`` for matching lines, streaming.

    Stops after ``max_matches`` matches without consuming further input.
    """
    if max_matches <= 0:
        raise ValueError("max_matches must be positive")
    found = 0
    for number, text in enumerate(lines, start=1):
        if matcher(text):
            yield number, text
            found += 1
            if found >= max_matches:
                return
