"""Find / replace over document lines (no Qt)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from re import Pattern

from magiceditor.core.safe_regex import compile_user_pattern
from magiceditor.core.text_match import (
    PatternError,
    expand_replacement,
    find_all_matches,
    find_first,
    find_last_before,
)

MAX_REPLACE_ALL = 50_000

LineText = Callable[[int], str]


@dataclass(frozen=True, slots=True)
class FindHit:
    line: int
    start: int
    end: int


def try_compile(
    needle: str,
    *,
    case_sensitive: bool = False,
    use_regex: bool = False,
) -> Pattern[str] | None:
    if not needle:
        return None
    try:
        return compile_user_pattern(needle, case_sensitive=case_sensitive, use_regex=use_regex)
    except PatternError:
        return None


def find_next_in_lines(
    line_text: LineText,
    n_lines: int,
    pattern: Pattern[str],
    *,
    start_line: int,
    start_col: int,
    last_match_start: int = -1,
    last_match_end: int = 0,
    backward: bool = False,
    wrap: bool = True,
) -> FindHit | None:
    """Next match after the caret, optionally wrapping."""
    if n_lines <= 0:
        return None
    start_line = max(0, min(start_line, n_lines - 1))
    if backward:
        order = list(range(start_line, -1, -1))
        if wrap:
            order += list(range(n_lines - 1, start_line, -1))
    else:
        order = list(range(start_line, n_lines))
        if wrap:
            order += list(range(0, start_line))

    for line in order:
        try:
            text = line_text(line)
        except IndexError:
            continue
        if backward:
            before = start_col if line == start_line else len(text) + 1
            m = find_last_before(text, pattern, before=before)
        else:
            col = 0
            if line == start_line:
                col = last_match_end if start_col == last_match_start else start_col
            m = find_first(text, pattern, start=col)
        if m is None:
            continue
        return FindHit(line, m.start(), m.end())
    return None


def collect_replace_jobs(
    line_text: LineText,
    n_lines: int,
    pattern: Pattern[str],
    replacement: str,
    *,
    use_regex: bool = False,
    max_replacements: int = MAX_REPLACE_ALL,
) -> list[tuple[int, int, int, str]]:
    """(line, start_col, end_col, expanded) from the end of the file."""
    jobs: list[tuple[int, int, int, str]] = []
    cap = max(1, int(max_replacements))
    for line in range(n_lines - 1, -1, -1):
        try:
            text = line_text(line)
        except IndexError:
            continue
        matches = find_all_matches(text, pattern)
        for m in reversed(matches):
            repl = expand_replacement(m, replacement) if use_regex else replacement
            jobs.append((line, m.start(), m.end(), repl))
            if len(jobs) >= cap:
                return jobs
    return jobs


def count_matches_in_lines(
    line_text: LineText,
    n_lines: int,
    pattern: Pattern[str],
    *,
    cap: int = 100_000,
) -> int:
    """Count matches line-by-line (K6). Never joins the buffer into one str."""
    total = 0
    limit = max(1, int(cap))
    for line in range(max(0, n_lines)):
        try:
            text = line_text(line)
        except IndexError:
            continue
        total += len(find_all_matches(text, pattern))
        if total >= limit:
            return total
    return total


def match_at_column(text: str, pattern: Pattern[str], col: int):
    return pattern.match(text, col)


def find_in_editor(
    editor,
    needle: str,
    *,
    case_sensitive: bool = False,
    backward: bool = False,
    wrap: bool = True,
    use_regex: bool = False,
) -> bool:
    pattern = try_compile(needle, case_sensitive=case_sensitive, use_regex=use_regex)
    if pattern is None:
        return False
    editor.set_find_highlight(needle, case_sensitive=case_sensitive, use_regex=use_regex)
    idx = editor._doc.line_index()
    n_lines = idx.line_count
    hit = find_next_in_lines(
        editor._doc.line_text,
        n_lines,
        pattern,
        start_line=editor._cursor_line,
        start_col=editor._cursor_col,
        last_match_start=editor._last_match_start_col,
        last_match_end=editor._last_match_end_col,
        backward=backward,
        wrap=wrap,
    )
    if hit is None:
        return False
    editor._cursor_line = hit.line
    editor._cursor_col = hit.start
    editor._last_match_start_col = hit.start
    editor._last_match_end_col = hit.end
    editor._ensure_visible(hit.line)
    editor.cursorPositionChanged.emit()
    editor.viewport().update()
    return True


def replace_in_editor(
    editor,
    needle: str,
    replacement: str,
    *,
    case_sensitive: bool = False,
    use_regex: bool = False,
) -> bool:
    pattern = try_compile(needle, case_sensitive=case_sensitive, use_regex=use_regex)
    if pattern is None:
        return False
    editor.set_find_highlight(needle, case_sensitive=case_sensitive, use_regex=use_regex)
    text = editor._doc.line_text(editor._cursor_line)
    m = match_at_column(text, pattern, editor._cursor_col)
    if m is None:
        if not find_in_editor(
            editor,
            needle,
            case_sensitive=case_sensitive,
            backward=False,
            wrap=True,
            use_regex=use_regex,
        ):
            return False
        text = editor._doc.line_text(editor._cursor_line)
        m = match_at_column(text, pattern, editor._cursor_col)
        if m is None:
            return False
    repl = expand_replacement(m, replacement) if use_regex else replacement
    editor._replace_char_span(editor._cursor_line, m.start(), m.end(), repl)
    return True


def replace_all_in_editor(
    editor,
    needle: str,
    replacement: str,
    *,
    case_sensitive: bool = False,
    use_regex: bool = False,
    max_replacements: int = MAX_REPLACE_ALL,
) -> int:
    pattern = try_compile(needle, case_sensitive=case_sensitive, use_regex=use_regex)
    if pattern is None:
        return 0
    editor.set_find_highlight(needle, case_sensitive=case_sensitive, use_regex=use_regex)
    n_lines = editor._doc.line_index().line_count
    jobs = collect_replace_jobs(
        editor._doc.line_text,
        n_lines,
        pattern,
        replacement,
        use_regex=use_regex,
        max_replacements=max_replacements,
    )
    count = 0
    for line, start_col, end_col, repl in jobs:
        try:
            editor._replace_char_span(line, start_col, end_col, repl, emit=False)
        except (IndexError, ValueError):
            continue
        count += 1
    if count:
        editor._cursor_line = min(editor._cursor_line, editor._line_count() - 1)
        editor._cursor_col = min(
            editor._cursor_col, len(editor._doc.line_text(editor._cursor_line))
        )
        editor._emit_edit()
    return count


def replace_char_span(
    editor,
    line: int,
    start_col: int,
    end_col: int,
    replacement: str,
    *,
    emit: bool = True,
) -> None:
    enc = editor._doc.encoding if editor._doc.encoding != "utf-8-sig" else "utf-8"
    line_start = editor._doc.line_index().line_start(line)
    off = line_start + editor._col_to_byte(line, start_col)
    end_off = line_start + editor._col_to_byte(line, end_col)
    if end_off > off:
        editor._delete_bytes_tracked(off, end_off - off)
    repl_b = replacement.encode(enc, errors="replace")
    if repl_b:
        editor._insert_bytes_tracked(off, repl_b)
    if emit:
        editor._place_cursor_at(off + len(repl_b))
        editor._last_match_start_col = -1
        editor._last_match_end_col = 0
        editor._emit_edit()
