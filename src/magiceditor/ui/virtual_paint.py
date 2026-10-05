"""Viewport paint for VirtualEditor (visible lines only)."""

from __future__ import annotations

import re

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPaintEvent

from magiceditor.core.line_wrap import expand_tabs
from magiceditor.core.multi_cursor import word_at
from magiceditor.core.safe_regex import compile_user_pattern
from magiceditor.core.text_match import PatternError, find_all_matches
from magiceditor.ui.syntax_paint import paint_syntax_line
from magiceditor.ui.virtual_metrics import scroll_origin

FIND_BG = QColor(234, 179, 8, 90)
OCCUR_BG = QColor(234, 179, 8, 40)


def mono_advance(text: str, char_w: int) -> int:
    """Monospace prefix width (K4) — avoid per-glyph horizontalAdvance."""
    return max(0, int(char_w)) * len(text)


def paint_event(editor, event: QPaintEvent | None) -> None:
    painter = QPainter(editor.viewport())
    aa = bool(getattr(editor, "_antialiasing", True))
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, aa)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, aa)
    painter.fillRect(editor.viewport().rect(), editor._bg)
    painter.setFont(editor.font())
    fm = editor.fontMetrics()
    lh = editor._line_height
    first, skip = scroll_origin(editor)
    space_w = fm.horizontalAdvance(" ")
    h_off = 0 if editor._word_wrap else editor.horizontalScrollBar().value() * space_w
    gutter = editor._gutter_width if editor._show_line_numbers else 0
    total = editor._line_count()
    doc_syntax = getattr(getattr(editor, "_doc", None), "syntax_enabled", True)
    do_syntax = editor._syntax_enabled and doc_syntax and editor._language not in {"", "text"}
    view_h = editor.viewport().height()

    if gutter:
        painter.fillRect(0, 0, gutter, view_h, editor._gutter_bg)

    margin_cols = int(getattr(editor, "_right_margin", 0) or 0)
    if margin_cols > 0 and not editor._word_wrap:
        mx = gutter + editor._pad_x + margin_cols * space_w - h_off
        margin_color = QColor(editor._gutter_fg)
        margin_color.setAlpha(90)
        painter.setPen(margin_color)
        painter.drawLine(int(mx), 0, int(mx), view_h)

    highlight = bool(getattr(editor, "_highlight_occurrences", False))
    occur_re = _occurrence_pattern(editor) if highlight else None

    y = 0
    line = first
    while y < view_h and line < total:
        try:
            text = editor._doc.line_text(line)
        except IndexError:
            text = ""
        rows = editor._wrap_display_rows(text)
        if skip and line == first:
            # Sub-row scroll inside the last (giant) line: drop rows already
            # scrolled above the viewport — ry = y + (ri - skip) * lh.
            rows = rows[skip:]
        row_h = lh * len(rows)
        if line == editor._cursor_line and editor._highlight_current_line:
            painter.fillRect(
                gutter,
                y,
                editor.viewport().width() - gutter,
                row_h,
                editor._line_hl,
            )
        if gutter:
            if line in editor._bookmarks:
                painter.setBrush(editor._bookmark_color)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(4, y + lh // 2 - 4, 8, 8)
            num = str(line + 1)
            painter.setPen(
                editor._gutter_fg_active if line == editor._cursor_line else editor._gutter_fg
            )
            painter.drawText(
                0,
                y,
                gutter - 8,
                lh,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                num,
            )

        base_x = gutter + editor._pad_x - h_off
        if (
            getattr(editor, "_indent_guides", False)
            and not editor._word_wrap
            and text
            and len(text) <= 8000
        ):
            _paint_indent_guides(editor, painter, text, gutter, space_w, h_off, y, row_h)
        sel_cols = editor._selection_cols_on_line(line)
        for ri, (d0, d1, row) in enumerate(rows):
            ry = y + ri * lh
            if ry > view_h:
                break
            baseline = ry + fm.ascent() + 1
            if sel_cols is not None:
                paint_selection_row(editor, painter, text, sel_cols, d0, d1, base_x, ry, lh, fm)
            if editor._find_needle:
                paint_find_hits_row(editor, painter, text, d0, d1, base_x, ry, lh, fm)
            if occur_re is not None and text and len(text) <= 8000:
                paint_occurrence_row(painter, text, occur_re, d0, d1, base_x, ry, lh, fm)
            if editor._spell is not None and text and len(text) <= 4000:
                paint_spell_row(editor, painter, text, d0, d1, base_x, ry, lh, fm, line)
            if do_syntax and text and len(text) <= 8000:
                cache = getattr(editor, "_token_cache", None)
                tokens = cache.tokens(line, text, editor._language) if cache is not None else None
                paint_syntax_line(
                    painter,
                    text=text,
                    display=row,
                    language=editor._language,
                    base_x=base_x,
                    baseline=baseline,
                    fm=fm,
                    font=editor.font(),
                    default_fg=editor._fg,
                    light=editor._syntax_light,
                    col_start=d0,
                    col_end=d1,
                    tokens=tokens,
                    char_width=space_w,
                )
            else:
                painter.setPen(editor._fg)
                if not editor._word_wrap and len(row) > 300:
                    vis_col_start = max(0, int((h_off - editor._pad_x) // space_w))
                    vis_cols = (editor.viewport().width() - gutter) // space_w + 4
                    vis_col_end = vis_col_start + int(vis_cols)
                    sub_row = row[vis_col_start:vis_col_end]
                    sub_x = base_x + mono_advance(row[:vis_col_start], space_w)
                    painter.drawText(sub_x, baseline, sub_row)
                else:
                    painter.drawText(base_x, baseline, row)
            if editor._show_whitespace and row:
                paint_whitespace(editor, painter, row, base_x, ry, lh, fm)
            if (
                editor._brace_match_enabled
                and editor._brace_match_col is not None
                and editor._brace_line == line
                and d0 <= editor._brace_match_col < d1
            ):
                paint_brace_mark(painter, text, editor._brace_match_col, d0, base_x, ry, lh, fm)
            if (
                editor._brace_match_enabled
                and editor._brace_pair_col is not None
                and editor._brace_pair_line == line
                and d0 <= editor._brace_pair_col < d1
            ):
                paint_brace_mark(painter, text, editor._brace_pair_col, d0, base_x, ry, lh, fm)

            if line == editor._cursor_line:
                caret_disp = len(expand_tabs(text[: editor._cursor_col]))
                if d0 <= caret_disp <= d1:
                    prefix = row[: caret_disp - d0]
                    cw = max(1, fm.horizontalAdvance(" "))
                    cx = base_x + mono_advance(prefix, cw)
                    painter.setPen(editor._caret)
                    for dx in range(editor._caret_width):
                        painter.drawLine(cx + dx, ry + 1, cx + dx, ry + lh - 2)
            for el, esc, eec in editor._extra_cursors:
                if el != line:
                    continue
                caret_disp = len(expand_tabs(text[:esc]))
                if d0 <= caret_disp <= d1:
                    prefix = row[: caret_disp - d0]
                    cx = base_x + mono_advance(prefix, space_w)
                    painter.setPen(editor._caret)
                    painter.drawLine(cx, ry + 1, cx, ry + lh - 2)
                if esc != eec:
                    paint_selection_row(
                        editor, painter, text, (esc, eec), d0, d1, base_x, ry, lh, fm
                    )

        y += row_h
        line += 1


def _occurrence_pattern(editor):
    try:
        caret = editor._doc.line_text(editor._cursor_line)
    except IndexError:
        return None
    if len(caret) > 8000:
        return None
    hit = word_at([caret], 0, int(editor._cursor_col))
    if hit is None or not (2 <= len(hit[0]) <= 64):
        return None
    return re.compile(r"\b" + re.escape(hit[0]) + r"\b")


def _paint_indent_guides(
    editor,
    painter,
    text: str,
    gutter: int,
    space_w: int,
    h_off: int,
    y: int,
    row_h: int,
) -> None:
    guide = QColor(editor._gutter_fg)
    guide.setAlpha(70)
    painter.setPen(guide)
    tw = max(1, int(editor._tab_width))
    col = 0
    for ch in text:
        if ch == " ":
            col += 1
        elif ch == "\t":
            col += tw - (col % tw)
        else:
            break
        if col > 0 and col % tw == 0:
            gx = gutter + editor._pad_x + col * space_w - h_off
            painter.drawLine(int(gx), y, int(gx), y + row_h)


def paint_occurrence_row(painter, text: str, pattern, d0, d1, base_x, y, lh, fm) -> None:
    cw = max(1, fm.horizontalAdvance(" "))
    for m in pattern.finditer(text):
        md0 = len(expand_tabs(text[: m.start()]))
        md1 = len(expand_tabs(text[: m.end()]))
        if md1 <= d0 or md0 >= d1:
            continue
        a = max(md0, d0) - d0
        b = min(md1, d1) - d0
        row = expand_tabs(text)[d0:d1]
        x0 = base_x + mono_advance(row[:a], cw)
        w = mono_advance(row[a:b], cw)
        painter.fillRect(x0, y + 1, max(1, w), lh - 2, OCCUR_BG)


def paint_selection_row(
    editor, painter: QPainter, text: str, sel_cols: tuple[int, int], d0, d1, base_x, y, lh, fm
) -> None:
    a_col, b_col = sel_cols
    md0 = len(expand_tabs(text[:a_col]))
    md1 = len(expand_tabs(text[:b_col]))
    if md1 <= d0 or md0 >= d1:
        return
    a = max(md0, d0) - d0
    b = min(md1, d1) - d0
    row = expand_tabs(text)[d0:d1]
    x0 = base_x + mono_advance(row[:a], fm.horizontalAdvance(" "))
    w = mono_advance(row[a:b], fm.horizontalAdvance(" "))
    painter.fillRect(x0, y + 1, max(2, w), lh - 2, editor._sel_bg)


def paint_whitespace(editor, painter: QPainter, row: str, base_x, ry, lh, fm) -> None:
    dim = QColor(editor._gutter_fg)
    dim.setAlpha(110)
    painter.setPen(dim)
    cw = max(1, fm.horizontalAdvance(" "))
    x = base_x
    for ch in row:
        if ch == " ":
            painter.drawText(x, ry + lh - 4, "·")
        elif ch == "\t":
            painter.drawText(x, ry + lh - 4, "»")
        x += cw


def paint_spell_row(
    editor, painter: QPainter, text: str, d0, d1, base_x, ry, lh, fm, line: int
) -> None:
    ready = getattr(editor, "_spell_spans", None)
    if isinstance(ready, dict) and line in ready:
        spans = ready[line]
    else:
        return
    cw = max(1, fm.horizontalAdvance(" "))
    for start, end in spans:
        if end <= d0 or start >= d1:
            continue
        a = max(start, d0)
        b = min(end, d1)
        if d0 == 0:
            x0 = base_x + mono_advance(expand_tabs(text[:a]), cw)
        else:
            x0 = base_x + mono_advance(expand_tabs(text[d0:a]) if a >= d0 else "", cw)
        w = max(2, mono_advance(expand_tabs(text[a:b]), cw))
        painter.setPen(editor._spell_color)
        y_line = ry + lh - 2
        x = x0
        amp = 2
        while x < x0 + w:
            x2 = min(x + 3, x0 + w)
            painter.drawLine(int(x), y_line + amp, int(x2), y_line - amp)
            x = x2
            amp = -amp


def paint_brace_mark(painter: QPainter, text: str, col: int, d0, base_x, ry, lh, fm) -> None:
    if col < d0:
        return
    cw = max(1, fm.horizontalAdvance(" "))
    x0 = base_x + mono_advance(expand_tabs(text[d0:col]), cw)
    w = cw
    painter.fillRect(x0, ry + lh - 3, max(2, w), 2, QColor(255, 215, 0, 200))


def paint_find_hits_row(editor, painter: QPainter, text: str, d0, d1, base_x, y, lh, fm) -> None:
    needle = editor._find_needle
    if not needle or not text:
        return
    try:
        pattern = compile_user_pattern(
            needle,
            case_sensitive=editor._find_case,
            use_regex=editor._find_regex,
        )
    except PatternError:
        return
    cw = max(1, fm.horizontalAdvance(" "))
    for m in find_all_matches(text, pattern):
        md0 = len(expand_tabs(text[: m.start()]))
        md1 = len(expand_tabs(text[: m.end()]))
        if md1 <= d0 or md0 >= d1:
            continue
        a = max(md0, d0) - d0
        b = min(md1, d1) - d0
        row = expand_tabs(text)[d0:d1]
        x0 = base_x + mono_advance(row[:a], cw)
        w = mono_advance(row[a:b], cw)
        painter.fillRect(x0, y + 1, max(1, w), lh - 2, FIND_BG)
