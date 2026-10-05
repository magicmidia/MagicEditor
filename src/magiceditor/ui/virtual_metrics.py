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
    extra = max(0, min(16, int(getattr(editor, "_line_spacing", 0) or 0)))
    editor._line_height = max(14, editor.fontMetrics().height() + 2 + extra)
    update_scrollbars(editor)


def update_scrollbars(editor) -> None:
    lines = line_count(editor)
    visible = visible_line_slots(editor)
    if editor._word_wrap:
        max_scroll = _wrapped_max_scroll(editor, lines, visible)
        # Sub-row scroll: when the last line alone wraps to more display rows
        # than the viewport, its tail rows are unreachable at ``lines - 1``.
        try:
            tail_rows = len(editor._wrap_display_rows(editor._doc.line_text(lines - 1)))
        except IndexError:
            tail_rows = 1
        max_scroll += max(0, tail_rows - visible)
    else:
        # Flush: last document line occupies the last visible row (no empty pad).
        max_scroll = max(0, lines - visible)
    editor.verticalScrollBar().setRange(0, max_scroll)
    editor.verticalScrollBar().setPageStep(visible)
    if editor._word_wrap:
        editor.horizontalScrollBar().setRange(0, 0)
    else:
        editor.horizontalScrollBar().setRange(0, 200)
        editor.horizontalScrollBar().setPageStep(20)


def _wrapped_max_scroll(editor, lines: int, visible: int) -> int:
    """First scroll value where the wrapped document end is fully visible.

    With word wrap on, one document line can occupy several display rows, so
    ``lines - visible`` under-scrolls: the tail (incl. the last line) renders
    past the viewport bottom, clipped against the status footer. Walk the tail
    accumulating display rows until the viewport is covered; the result keeps
    the last line flush at the bottom with no synthetic padding.
    """
    acc = 0
    v = lines
    while v > 0 and acc <= visible:
        v -= 1
        try:
            text = editor._doc.line_text(v)
        except IndexError:
            break
        acc += max(1, len(editor._wrap_display_rows(text)))
    if acc <= visible:
        return 0  # whole document fits in the viewport
    return min(v + 1, max(0, lines - 1))


def scroll_origin(editor) -> tuple[int, int]:
    """First painted ``(doc_line, skipped_rows)`` for the current scroll value.

    Normally ``(scrollbar value, 0)``. In wrap mode values past ``lines - 1``
    scroll *inside* the last line: ``(lines - 1, value - (lines - 1))``.
    """
    value = editor.verticalScrollBar().value()
    if not editor._word_wrap:
        return value, 0
    last = line_count(editor) - 1
    if value > last:
        return last, value - last
    return value, 0


def text_area_width(editor) -> int:
    gutter = editor._gutter_width if editor._show_line_numbers else 0
    return max(40, editor.viewport().width() - gutter - editor._pad_x * 2)


def wrap_display_rows(editor, text: str) -> list[tuple[int, int, str]]:
    display = expand_tabs(text)
    if not editor._word_wrap:
        return [(0, len(display), display)]
    fm = editor.fontMetrics()
    max_w = text_area_width(editor)
    char_w = max(1, fm.horizontalAdvance(" "))
    ranges = wrap_ranges(display, max_w, char_w)
    return [(a, b, display[a:b]) for a, b in ranges]


def _row_count(editor, line: int) -> int:
    try:
        text = editor._doc.line_text(line)
    except IndexError:
        return 1
    return max(1, len(editor._wrap_display_rows(text)))


def _caret_row(editor, line: int) -> int:
    """Display row of the caret inside ``line`` (0 = first wrapped row)."""
    try:
        text = editor._doc.line_text(line)
    except IndexError:
        return 0
    rows = editor._wrap_display_rows(text)
    if not rows:
        return 0
    col = int(getattr(editor, "_cursor_col", 0) or 0)
    col = max(0, min(col, len(text)))
    caret = len(expand_tabs(text[:col]))
    found = 0
    last = len(rows) - 1
    for i, (d0, d1, _row) in enumerate(rows):
        if d0 <= caret <= d1:
            found = i
            if caret < d1 or i == last:
                break
    return found


def _screen_row(editor, first: int, skip: int, line: int, caret_row: int) -> int | None:
    """Viewport row of the caret, or None when ``line`` is above the scroll origin."""
    if line < first:
        return None
    if line == first:
        return caret_row - skip
    y = 0
    for ln in range(first, line):
        n = _row_count(editor, ln)
        if ln == first:
            n = max(0, n - skip)
        y += n
    return y + caret_row


def _scroll_maximum(scrollbar) -> int:
    maximum = getattr(scrollbar, "maximum", None)
    if callable(maximum):
        return int(maximum())
    return int(getattr(scrollbar, "hi", 0))


def ensure_visible(editor, line: int) -> None:
    scrollbar = editor.verticalScrollBar()
    usable = max(1, usable_line_slots(editor))
    if not getattr(editor, "_word_wrap", False):
        first = scrollbar.value()
        if line < first:
            scrollbar.setValue(line)
        elif line >= first + usable:
            scrollbar.setValue(max(0, line - usable + 1))
        return

    # A wrapped row past the last slot is clipped by the status footer.
    # Scroll only when that row is off-screen, and keep the caret on the
    # last fully visible slot instead of jumping the line to the top.
    caret_row = _caret_row(editor, line)
    first, skip = scroll_origin(editor)
    screen = _screen_row(editor, first, skip, line, caret_row)
    if screen is not None and 0 <= screen < usable:
        return
    if caret_row >= usable:
        scrollbar.setValue(min(line, _scroll_maximum(scrollbar)))
        return
    remaining = usable - 1 - caret_row
    probe = line
    while probe > 0 and remaining > 0:
        count = _row_count(editor, probe - 1)
        if count > remaining:
            break
        remaining -= count
        probe -= 1
    if screen is not None and screen >= usable:
        probe = max(probe, first)
    scrollbar.setValue(max(0, min(probe, _scroll_maximum(scrollbar))))
