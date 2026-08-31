"""Scroll / wrap metrics for VirtualEditor (J1.1)."""

from __future__ import annotations

from magiceditor.core.line_wrap import expand_tabs, wrap_ranges


def line_count(editor) -> int:
    return max(1, editor._doc.line_index().line_count)


def visible_line_slots(editor) -> int:
    lh = max(1, int(getattr(editor, "_line_height", 1) or 1))
    return max(1, editor.viewport().height() // lh)


def usable_line_slots(editor) -> int:
    """Fully visible rows — last line sits flush against the status footer."""
    return visible_line_slots(editor)


def recalc_metrics(editor) -> None:
    editor._line_height = max(14, editor.fontMetrics().height() + 2)
    update_scrollbars(editor)


def update_scrollbars(editor) -> None:
    lines = line_count(editor)
    visible = visible_line_slots(editor)
    # Flush: last document line occupies the last visible row (no empty pad).
    editor.verticalScrollBar().setRange(0, max(0, lines - visible))
    editor.verticalScrollBar().setPageStep(visible)
    if editor._word_wrap:
        editor.horizontalScrollBar().setRange(0, 0)
    else:
        editor.horizontalScrollBar().setRange(0, 200)
        editor.horizontalScrollBar().setPageStep(20)


def text_area_width(editor) -> int:
    gutter = editor._gutter_width if editor._show_line_numbers else 0
    return max(40, editor.viewport().width() - gutter - editor._pad_x * 2)


def wrap_display_rows(editor, text: str) -> list[tuple[int, int, str]]:
    display = expand_tabs(text)
    if not editor._word_wrap:
        return [(0, len(display), display)]
    fm = editor.fontMetrics()
    max_w = text_area_width(editor)
    ranges = wrap_ranges(display, max_w, fm.horizontalAdvance)
    return [(a, b, display[a:b]) for a, b in ranges]


def ensure_visible(editor, line: int) -> None:
    first = editor.verticalScrollBar().value()
    usable = usable_line_slots(editor)
    if line < first:
        editor.verticalScrollBar().setValue(line)
    elif line >= first + usable:
        editor.verticalScrollBar().setValue(line - usable + 1)
