"""Paint syntax token spans on a virtual-editor line (visible slice only)."""

from __future__ import annotations

from PyQt6.QtGui import QColor, QFont, QPainter

from magiceditor.core.syntax.rules import tokenize_line
from magiceditor.ui.syntax_colors import palette_for


def paint_syntax_line(
    painter: QPainter,
    *,
    text: str,
    display: str,
    language: str,
    base_x: int,
    baseline: int,
    fm: object,
    font: QFont,
    default_fg: QColor,
    light: bool = False,
    col_start: int = 0,
    col_end: int | None = None,
    tokens: list[tuple[int, int, str]] | None = None,
    char_width: int | None = None,
) -> None:
    """Draw ``text`` tokens; only columns ``[col_start, col_end)`` (display slice)."""
    end = len(text) if col_end is None else min(col_end, len(text))
    start = max(0, col_start)
    palette = palette_for(light=light)
    spans = tokens if tokens is not None else tokenize_line(text, language)
    bold_font = QFont(font)
    bold_font.setBold(True)

    def advance(chunk: str) -> int:
        if char_width is not None:
            return max(0, int(char_width)) * len(chunk)
        return int(fm.horizontalAdvance(chunk))  # type: ignore[union-attr]

    def expand_slice(a: int, b: int) -> str:
        return text[a:b].replace("\t", "    ")

    claimed_end = start
    x = base_x
    for tok_start, length, kind in spans:
        tok_end = tok_start + length
        vis_a = max(tok_start, start)
        vis_b = min(tok_end, end)
        if vis_a >= vis_b:
            continue
        if vis_a > claimed_end:
            gap = expand_slice(claimed_end, vis_a)
            painter.setFont(font)
            painter.setPen(default_fg)
            painter.drawText(x, baseline, gap)
            x += advance(gap)
        chunk = expand_slice(vis_a, vis_b)
        color, bold = palette.get(kind, (default_fg.name(), False))
        painter.setFont(bold_font if bold else font)
        painter.setPen(QColor(color))
        painter.drawText(x, baseline, chunk)
        x += advance(chunk)
        claimed_end = vis_b

    if claimed_end < end:
        tail = expand_slice(claimed_end, end)
        painter.setFont(font)
        painter.setPen(default_fg)
        painter.drawText(x, baseline, tail)
    elif not spans:
        painter.setFont(font)
        painter.setPen(default_fg)
        painter.drawText(base_x, baseline, display)

    painter.setFont(font)
