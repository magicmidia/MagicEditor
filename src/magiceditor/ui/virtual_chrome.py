"""Theme, zoom, bookmarks, and pref setters for VirtualEditor (J1.1)."""

from __future__ import annotations

from PyQt6.QtGui import QColor

from magiceditor.themes.tokens import chrome_tokens, is_light_theme
from magiceditor.ui.fonts import editor_font


def apply_theme_palette(editor, theme_id: str) -> None:
    tok = chrome_tokens(theme_id)
    editor._syntax_light = is_light_theme(theme_id)
    accent = QColor(tok.accent)
    line_hl = QColor(accent)
    line_hl.setAlpha(28)
    sel = QColor(accent)
    sel.setAlpha(60)
    mark = QColor(accent)
    mark.setAlpha(220)
    gutter_bg = QColor(tok.surface)
    gutter_bg.setAlpha(80)
    editor._bg = QColor(tok.bg)
    editor._fg = QColor(tok.fg)
    editor._line_hl = line_hl
    editor._sel_bg = sel
    editor._caret = accent
    editor._gutter_bg = gutter_bg
    editor._gutter_fg = QColor(tok.muted)
    editor._gutter_fg_active = QColor(tok.heading)
    editor._bookmark_color = mark
    editor.viewport().update()


def zoom_in(editor) -> None:
    f = editor.font()
    f.setPointSize(min(48, f.pointSize() + 1))
    editor.setFont(f)
    editor._recalc_metrics()
    editor.viewport().update()


def zoom_out(editor) -> None:
    f = editor.font()
    f.setPointSize(max(8, f.pointSize() - 1))
    editor.setFont(f)
    editor._recalc_metrics()
    editor.viewport().update()


def zoom_reset(editor) -> None:
    base = getattr(editor, "_base_font_size", 12) or 12
    editor.setFont(editor_font(int(base)))
    editor._recalc_metrics()
    editor.viewport().update()


def set_font_point_size(editor, size: int) -> None:
    size = max(8, min(48, int(size)))
    editor._base_font_size = size
    f = editor.font()
    f.setPointSize(size)
    editor.setFont(f)
    editor._recalc_metrics()
    editor.viewport().update()


def toggle_bookmark(editor) -> None:
    line = editor._cursor_line
    if line in editor._bookmarks:
        editor._bookmarks.discard(line)
    else:
        editor._bookmarks.add(line)
    editor.viewport().update()


def next_bookmark(editor) -> bool:
    if not editor._bookmarks:
        return False
    after = sorted(b for b in editor._bookmarks if b > editor._cursor_line)
    target = after[0] if after else min(editor._bookmarks)
    editor.goto_line(target, 0)
    return True


def prev_bookmark(editor) -> bool:
    if not editor._bookmarks:
        return False
    before = sorted(b for b in editor._bookmarks if b < editor._cursor_line)
    target = before[-1] if before else max(editor._bookmarks)
    editor.goto_line(target, 0)
    return True


def update_brace_match(editor) -> None:
    from magiceditor.core.brace_match import brace_at_or_near, find_matching_brace

    editor._brace_match_col = None
    editor._brace_pair_col = None
    editor._brace_line = None
    editor._brace_pair_line = None
    if not getattr(editor, "_brace_match_enabled", True):
        return
    line = int(editor._cursor_line)
    # A debounced match can run after a replace or close left the caret past the end.
    if line < 0 or line >= editor._line_count():
        return
    text = editor._doc.line_text(line)
    bpos = brace_at_or_near(text, editor._cursor_col)
    if bpos is None:
        return
    match = find_matching_brace(text, bpos)
    if match is not None:
        editor._brace_line = line
        editor._brace_match_col = bpos
        editor._brace_pair_line = line
        editor._brace_pair_col = match
        return
    start = max(0, line - 80)
    end = min(editor._line_count(), line + 80)
    parts = [editor._doc.line_text(i) for i in range(start, end)]
    chunk = "\n".join(parts)
    off = 0
    for i in range(line - start):
        off += len(parts[i]) + 1
    off += bpos
    m = find_matching_brace(chunk, off)
    if m is None:
        editor._brace_line = line
        editor._brace_match_col = bpos
        return
    pos = 0
    for li, ln in enumerate(parts):
        if pos + len(ln) >= m:
            editor._brace_line = line
            editor._brace_match_col = bpos
            editor._brace_pair_line = start + li
            editor._brace_pair_col = m - pos
            return
        pos += len(ln) + 1


def apply_brace_enabled(editor, enabled: bool) -> None:
    editor._brace_match_enabled = bool(enabled)
    if not editor._brace_match_enabled:
        editor._brace_match_col = None
        editor._brace_pair_col = None
        editor._brace_line = None
        editor._brace_pair_line = None
    else:
        editor._update_brace_match()
    editor.viewport().update()
