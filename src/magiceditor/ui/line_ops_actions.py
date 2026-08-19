"""Line-ops / brace helpers used by the power mixin (J1.3)."""

from __future__ import annotations

from magiceditor.core.brace_match import brace_at_or_near, find_matching_brace
from magiceditor.core.comment_rules import toggle_line_comments
from magiceditor.core.document_edit import selection_or_all
from magiceditor.core.line_edit_range import swap_line_with_neighbor
from magiceditor.core.line_ops import (
    delete_blank_lines,
    join_lines,
    sort_lines,
    spaces_to_tabs,
    tabs_to_spaces,
    trim_trailing_whitespace,
)


def selection_line_range(editor) -> tuple[int | None, int | None]:
    if editor is None or not hasattr(editor, "has_selection"):
        return None, None
    if not editor.has_selection():
        return None, None
    s_line, _sc, e_line, _ec = editor._normalized_selection()
    return s_line, e_line


def apply_line_transform(document, editor, transform) -> None:
    a, b = selection_line_range(editor)
    if a is None and getattr(document, "huge_mode", False):
        from magiceditor.core.document_edit import transform_all_lines

        # K14: do not materialize a multi-GB buffer for whole-file sort/trim.
        transform_all_lines(document, transform, max_lines=20_000)
        return
    selection_or_all(document, sel_start_line=a, sel_end_line=b, transform=transform)


def move_line(document, cursor_line: int, *, up: bool) -> int:
    return swap_line_with_neighbor(document, cursor_line, up=up)


def comment_transform(language: str):
    def transform(ls: list[str]) -> list[str]:
        return toggle_line_comments(ls, language)

    return transform


def tab_width_transform(spaces_to_tabs_mode: bool, width: int):
    w = int(width or 4)
    if spaces_to_tabs_mode:
        return lambda ls: spaces_to_tabs(ls, w)
    return lambda ls: tabs_to_spaces(ls, w)


def matching_brace_target(
    chunk_lines: list[str],
    cursor_line: int,
    cursor_col: int,
    window_start: int,
) -> tuple[int, int] | None:
    """Map a brace match in a window of lines back to (line, col)."""
    chunk = "\n".join(chunk_lines)
    off = 0
    for i in range(cursor_line - window_start):
        off += len(chunk_lines[i]) + 1
    off += cursor_col
    bpos = brace_at_or_near(chunk, off)
    if bpos is None:
        return None
    match = find_matching_brace(chunk, bpos)
    if match is None:
        return None
    line = window_start
    pos = 0
    for ln in chunk_lines:
        if pos + len(ln) >= match:
            return line, match - pos
        pos += len(ln) + 1
        line += 1
    return None


# Re-export ops so the mixin need not import core.line_ops.
LINE_OPS = {
    "sort": sort_lines,
    "join": join_lines,
    "delete_blank": delete_blank_lines,
    "trim": trim_trailing_whitespace,
}
