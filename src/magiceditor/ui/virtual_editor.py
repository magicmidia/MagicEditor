"""Virtual viewport editor — paints only visible lines from a piece table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from PyQt6.QtCore import QEvent, QPoint, Qt, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QContextMenuEvent,
    QFont,
    QGuiApplication,
    QKeyEvent,
    QPainter,
    QPaintEvent,
    QWheelEvent,
)
from PyQt6.QtWidgets import QAbstractScrollArea, QWidget

from magiceditor.core.brace_match import brace_at_or_near, find_matching_brace
from magiceditor.core.line_wrap import expand_tabs, wrap_ranges
from magiceditor.core.multi_cursor import restore_carets_after_multi_insert, word_at
from magiceditor.core.snippets import expand_snippet, match_trigger
from magiceditor.core.spell import SpellEngine
from magiceditor.core.syntax.rules import tokenize_line
from magiceditor.core.text_match import (
    PatternError,
    compile_pattern,
    expand_replacement,
    find_all_matches,
    find_first,
    find_last_before,
)
from magiceditor.services.document import Document
from magiceditor.ui.fonts import editor_font

# kind -> (fg hex, bold) — match MagicHighlighter dark palette
_SYNTAX_PALETTE: dict[str, tuple[str, bool]] = {
    "keyword": ("#C792EA", True),
    "string": ("#C3E88D", False),
    "comment": ("#546E7A", False),
    "number": ("#F78C6C", False),
    "decorator": ("#82AAFF", False),
    "heading": ("#82AAFF", True),
    "code": ("#89DDFF", False),
    "link": ("#80CBC4", False),
}
_DEFAULT_FG = "#E2E8F0"
_FIND_BG = QColor(234, 179, 8, 90)
_MAX_REPLACE_ALL = 50_000
_MAX_UNDO = 500
_MAX_CLIPBOARD = 8 * 1024 * 1024


@dataclass(slots=True)
class _EditOp:
    kind: Literal["insert", "delete"]
    offset: int
    data: bytes


class VirtualEditor(QAbstractScrollArea):
    """Huge-file viewer/editor surface.

    Does **not** load the full document into a ``QTextDocument``. Lines are
    fetched from the document piece table on paint. Editing mutates the
    piece table and keeps the line index incremental.
    """

    cursorPositionChanged = pyqtSignal()
    textChanged = pyqtSignal()
    modificationChanged = pyqtSignal(bool)
    # Global screen position for right-click / context menu (MainWindow wires QMenu).
    context_menu_requested = pyqtSignal(QPoint)

    def __init__(self, document: Document, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._doc = document
        self._show_line_numbers = True
        self._word_wrap = False
        self._tab_width = 4
        self._indent_with_spaces = True
        self._highlight_current_line = True
        self._base_font_size = 12
        self._bookmarks: set[int] = set()
        self._cursor_line = 0
        self._cursor_col = 0
        self._anchor_line: int | None = None
        self._anchor_col = 0
        self._selecting = False
        self._modified = False
        self._line_height = 18
        self._gutter_width = 56
        self._pad_x = 8
        self._language = "text"
        self._syntax_enabled = True
        self._brace_match_enabled = True
        self._show_whitespace = False
        self._caret_width = 1
        self._context_menu_enabled = True
        self._context_menu_from_mouse = False

        self._find_needle = ""
        self._find_case = False
        self._find_regex = False
        self._last_match_start_col = -1
        self._last_match_end_col = 0
        self._undo: list[_EditOp] = []
        self._redo: list[_EditOp] = []
        self._applying_history = False
        # Multi-cursor: list of (line, start_col, end_col)
        self._extra_cursors: list[tuple[int, int, int]] = []
        # Column (block) selection mode
        self._column_mode = False
        self._column_anchor: tuple[int, int] | None = None
        # Spell (viewport only)
        self._spell: SpellEngine | None = None
        self._spell_color = QColor(239, 68, 68, 220)
        self._brace_match_col: int | None = None
        self._brace_pair_col: int | None = None
        self._brace_line: int | None = None
        self._brace_pair_line: int | None = None
        self._word_completion = False
        self._completion_candidates: list[str] = []
        self._completion_index = 0
        # Palette (Luminous Void defaults — yellow caret like mockup)
        self._bg = QColor(14, 14, 14)
        self._fg = QColor(229, 226, 225)
        self._gutter_bg = QColor(127, 127, 127, 18)
        self._line_hl = QColor(255, 215, 0, 22)
        self._sel_bg = QColor(255, 215, 0, 55)
        self._caret = QColor(255, 215, 0)
        self._gutter_fg = QColor(153, 144, 119)
        self._gutter_fg_active = QColor(255, 246, 223)
        self._bookmark_color = QColor(255, 215, 0, 220)

        self.setFont(editor_font(12))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFrameShape(self.Shape.NoFrame)
        self.viewport().setCursor(Qt.CursorShape.IBeamCursor)
        # Context menu: QAbstractScrollArea delivers ContextMenu to this widget
        # via viewportEvent — policy on both self and viewport for reliability.
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)
        self.viewport().setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)
        self._recalc_metrics()
        self._update_scrollbars()

    def set_context_menu_enabled(self, enabled: bool) -> None:
        """Enable/disable right-click menu emission (settings toggle)."""
        self._context_menu_enabled = bool(enabled)

    def _emit_context_menu(self, global_pos: QPoint) -> None:
        if self._context_menu_enabled:
            self.context_menu_requested.emit(global_pos)

    # --- public API (parity helpers for EditorTab / dialogs) ------------

    def document_model(self) -> Document:
        return self._doc

    def is_huge_mode(self) -> bool:
        return True

    def set_language(self, language: str) -> None:
        if language == self._language:
            return
        self._language = language
        self.viewport().update()

    def language(self) -> str:
        return self._language

    def set_spell_engine(self, engine: SpellEngine | None) -> None:
        """Attach viewport spell checker (None disables)."""
        self._spell = engine
        self.viewport().update()

    def clear_extra_cursors(self) -> None:
        self._extra_cursors.clear()
        self.viewport().update()

    def extra_cursor_count(self) -> int:
        return len(self._extra_cursors)

    def set_column_mode(self, enabled: bool) -> None:
        self._column_mode = enabled
        if not enabled:
            self._column_anchor = None
        self.viewport().update()

    def is_column_mode(self) -> bool:
        return self._column_mode

    def set_word_completion(self, enabled: bool) -> None:
        self._word_completion = bool(enabled)

    def word_completion_enabled(self) -> bool:
        return self._word_completion

    def _column_rect(self) -> tuple[int, int, int, int] | None:
        """Return (start_line, end_line, col0, col1) for column selection, or None."""
        if not self._column_mode or not self.has_selection():
            return None
        s_line, s_col, e_line, e_col = self._normalized_selection()
        c0, c1 = min(s_col, e_col), max(s_col, e_col)
        return s_line, e_line, c0, c1

    def _multi_edit_spans(self) -> list[tuple[int, int, int]]:
        """Spans (line, start_col, end_col) for multi-cursor / column edits.

        Sorted bottom-to-top so byte offsets stay valid when applying deletes/inserts.
        """
        col = self._column_rect()
        if col is not None:
            s_line, e_line, c0, c1 = col
            spans = [(ln, c0, c1) for ln in range(s_line, e_line + 1)]
            spans.sort(key=lambda t: (t[0], t[1]), reverse=True)
            return spans
        if self._extra_cursors:
            spans: list[tuple[int, int, int]] = []
            if self.has_selection():
                s_line, s_col, e_line, e_col = self._normalized_selection()
                if s_line == e_line:
                    spans.append((s_line, s_col, e_col))
                else:
                    # stream multi-line + extras: fall back to stream for primary only
                    return []
            else:
                spans.append((self._cursor_line, self._cursor_col, self._cursor_col))
            for el, esc, eec in self._extra_cursors:
                spans.append((el, esc, eec))
            # dedupe
            seen: set[tuple[int, int, int]] = set()
            uniq: list[tuple[int, int, int]] = []
            for sp in spans:
                if sp not in seen:
                    seen.add(sp)
                    uniq.append(sp)
            uniq.sort(key=lambda t: (t[0], t[1]), reverse=True)
            return uniq
        return []

    def _update_brace_match(self) -> None:
        self._brace_match_col = None
        self._brace_pair_col = None
        self._brace_line = None
        self._brace_pair_line = None
        if not getattr(self, "_brace_match_enabled", True):
            return
        # Only scan current line + neighbors for performance
        line = self._cursor_line
        text = self._doc.line_text(line)
        bpos = brace_at_or_near(text, self._cursor_col)
        if bpos is None:
            return
        # Prefer same-line match first
        match = find_matching_brace(text, bpos)
        if match is not None:
            self._brace_line = line
            self._brace_match_col = bpos
            self._brace_pair_line = line
            self._brace_pair_col = match
            return
        # Multi-line window
        start = max(0, line - 80)
        end = min(self._line_count(), line + 80)
        parts: list[str] = []
        for i in range(start, end):
            parts.append(self._doc.line_text(i))
        chunk = "\n".join(parts)
        off = 0
        for i in range(line - start):
            off += len(parts[i]) + 1
        off += bpos
        m = find_matching_brace(chunk, off)
        if m is None:
            self._brace_line = line
            self._brace_match_col = bpos
            return
        # map m back
        pos = 0
        for li, ln in enumerate(parts):
            if pos + len(ln) >= m:
                self._brace_line = line
                self._brace_match_col = bpos
                self._brace_pair_line = start + li
                self._brace_pair_col = m - pos
                return
            pos += len(ln) + 1

    def set_find_highlight(
        self,
        needle: str,
        *,
        case_sensitive: bool = False,
        use_regex: bool = False,
    ) -> None:
        self._find_needle = needle
        self._find_case = case_sensitive
        self._find_regex = use_regex
        self.viewport().update()

    def goto_line(self, line: int, column: int = 0) -> None:
        """Move caret to 0-based line/column and scroll into view."""
        total = self._line_count()
        self._cursor_line = max(0, min(total - 1, line))
        text = self._doc.line_text(self._cursor_line)
        self._cursor_col = max(0, min(len(text), column))
        self._clear_selection()
        self._ensure_visible(self._cursor_line)
        self.cursorPositionChanged.emit()
        self.viewport().update()

    # --- clipboard / selection ----------------------------------------

    def has_selection(self) -> bool:
        return self._anchor_line is not None and (
            self._anchor_line != self._cursor_line or self._anchor_col != self._cursor_col
        )

    def replace_word_on_line(
        self, line: int, start_col: int, end_col: int, new_text: str
    ) -> None:
        """Replace [start_col, end_col) on *line* with *new_text* (spell apply)."""
        total = self._line_count()
        if line < 0 or line >= total:
            return
        text = self._doc.line_text(line)
        a = max(0, min(start_col, len(text)))
        b = max(a, min(end_col, len(text)))
        self._extra_cursors.clear()
        self._column_mode = False
        self._column_anchor = None
        self._cursor_line = line
        self._anchor_line = line
        self._anchor_col = a
        self._cursor_col = b
        if b > a:
            self._delete_selection(emit=False)
        self._insert_at_cursor(new_text)
        self._ensure_visible(line)
        self.viewport().update()

    def selected_text(self) -> str:
        if not self.has_selection():
            return ""
        s_line, s_col, e_line, e_col = self._normalized_selection()
        if s_line == e_line:
            return self._doc.line_text(s_line)[s_col:e_col]
        parts: list[str] = [self._doc.line_text(s_line)[s_col:]]
        # Cap huge multi-line selections for clipboard safety.
        max_lines = 50_000
        for ln in range(s_line + 1, min(e_line, s_line + max_lines)):
            parts.append(self._doc.line_text(ln))
        if e_line - s_line < max_lines:
            parts.append(self._doc.line_text(e_line)[:e_col])
        text = "\n".join(parts)
        if len(text) > _MAX_CLIPBOARD:
            return text[:_MAX_CLIPBOARD]
        return text

    def copy(self) -> None:
        text = self.selected_text()
        if not text:
            # Fallback: copy current line (editor habit)
            text = self._doc.line_text(self._cursor_line)
        if text:
            QGuiApplication.clipboard().setText(text)

    def cut(self) -> None:
        if self.has_selection():
            text = self.selected_text()
            if text:
                QGuiApplication.clipboard().setText(text)
            self._delete_selection()
            return
        # No selection: cut the current line (with trailing newline when present).
        line = self._cursor_line
        total = self._line_count()
        start = self._doc.line_index().line_start(line)
        if line < total - 1:
            end = self._doc.line_index().line_start(line + 1)
            text = self._doc.line_text(line) + "\n"
        else:
            content = self._doc.line_text(line)
            end = start + self._col_to_byte(line, len(content))
            text = content
        if text:
            QGuiApplication.clipboard().setText(text)
        if end > start:
            self._delete_bytes_tracked(start, end - start)
            self._place_cursor_at(start)
            self._emit_edit()

    def paste(self) -> None:
        text = QGuiApplication.clipboard().text()
        if not text:
            return
        if len(text) > _MAX_CLIPBOARD:
            text = text[:_MAX_CLIPBOARD]
        if self.has_selection():
            self._delete_selection(emit=False)
        self._insert_at_cursor(text)

    def select_all(self) -> None:
        total = self._line_count()
        if total <= 0:
            return
        self._anchor_line = 0
        self._anchor_col = 0
        last = total - 1
        self._cursor_line = last
        self._cursor_col = len(self._doc.line_text(last))
        self.cursorPositionChanged.emit()
        self.viewport().update()

    def _clear_selection(self) -> None:
        self._anchor_line = None
        self._anchor_col = 0

    def _normalized_selection(self) -> tuple[int, int, int, int]:
        assert self._anchor_line is not None
        a = (self._anchor_line, self._anchor_col)
        b = (self._cursor_line, self._cursor_col)
        if a <= b:
            return a[0], a[1], b[0], b[1]
        return b[0], b[1], a[0], a[1]

    def _selection_cols_on_line(self, line: int) -> tuple[int, int] | None:
        if not self.has_selection():
            # multi-cursor highlights
            for el, esc, eec in self._extra_cursors:
                if el == line and eec > esc:
                    return esc, eec
            return None
        col = self._column_rect()
        if col is not None:
            s_line, e_line, c0, c1 = col
            if line < s_line or line > e_line:
                return None
            text = self._doc.line_text(line)
            a = min(c0, len(text))
            b = min(c1, len(text))
            if a >= b:
                # zero-width column caret still paints nothing; OK
                return None if a == b else (a, b)
            return a, b
        s_line, s_col, e_line, e_col = self._normalized_selection()
        if line < s_line or line > e_line:
            return None
        a = s_col if line == s_line else 0
        b = e_col if line == e_line else len(self._doc.line_text(line))
        if a >= b:
            return None
        return a, b

    def _delete_selection(self, *, emit: bool = True) -> bool:
        if not self.has_selection() and not self._extra_cursors:
            return False
        spans = self._multi_edit_spans()
        if spans:
            # rectangular / multi-cursor delete (bottom-up)
            last_pos: tuple[int, int] | None = None
            for line, c0, c1 in spans:
                text = self._doc.line_text(line)
                a = min(c0, len(text))
                b = min(max(c1, c0), len(text))
                if b > a:
                    start = self._doc.line_index().line_start(line) + self._col_to_byte(
                        line, a
                    )
                    end = self._doc.line_index().line_start(line) + self._col_to_byte(
                        line, b
                    )
                    self._delete_bytes_tracked(start, end - start)
                last_pos = (line, a)
            self._extra_cursors.clear()
            self._column_mode = False
            self._column_anchor = None
            self._clear_selection()
            if last_pos is not None:
                self._cursor_line, self._cursor_col = last_pos
            if emit:
                self._emit_edit()
            return True
        if not self.has_selection():
            return False
        s_line, s_col, e_line, e_col = self._normalized_selection()
        start = self._doc.line_index().line_start(s_line) + self._col_to_byte(s_line, s_col)
        end = self._doc.line_index().line_start(e_line) + self._col_to_byte(e_line, e_col)
        if end > start:
            self._delete_bytes_tracked(start, end - start)
        self._place_cursor_at(start)
        self._clear_selection()
        if emit:
            self._emit_edit()
        return True

    def _begin_selection_if_needed(self, shift: bool) -> None:
        if shift:
            if self._anchor_line is None:
                self._anchor_line = self._cursor_line
                self._anchor_col = self._cursor_col
        else:
            self._clear_selection()

    def toPlainText(self) -> str:
        # Avoid materializing multi-GB strings casually.
        limit = 2 * 1024 * 1024
        raw = self._doc.buffer.get_text(0, min(len(self._doc.buffer), limit))
        enc = self._doc.encoding if self._doc.encoding != "utf-8-sig" else "utf-8"
        text = raw.decode(enc, errors="replace")
        if len(self._doc.buffer) > limit:
            text += "\n\n… [truncated for export — open smaller range or use external tools]"
        return text

    def set_line_numbers_visible(self, visible: bool) -> None:
        self._show_line_numbers = visible
        self._gutter_width = 56 if visible else 0
        self.viewport().update()

    def set_word_wrap(self, enabled: bool) -> None:
        self._word_wrap = enabled

    def set_font_point_size(self, size: int) -> None:
        size = max(8, min(48, int(size)))
        self._base_font_size = size
        f = self.font()
        f.setPointSize(size)
        self.setFont(f)
        self._recalc_metrics()
        self.viewport().update()

    def set_tab_width(self, width: int) -> None:
        self._tab_width = max(2, min(8, int(width)))

    def set_indent_with_spaces(self, enabled: bool) -> None:
        self._indent_with_spaces = bool(enabled)

    def set_highlight_current_line(self, enabled: bool) -> None:
        self._highlight_current_line = bool(enabled)
        self.viewport().update()

    def set_syntax_enabled(self, enabled: bool) -> None:
        self._syntax_enabled = bool(enabled)
        self.viewport().update()

    def set_brace_match_enabled(self, enabled: bool) -> None:
        self._brace_match_enabled = bool(enabled)
        if not self._brace_match_enabled:
            self._brace_match_col = None
            self._brace_pair_col = None
            self._brace_line = None
            self._brace_pair_line = None
        else:
            self._update_brace_match()
        self.viewport().update()

    def set_show_whitespace(self, enabled: bool) -> None:
        self._show_whitespace = bool(enabled)
        self.viewport().update()

    def set_caret_width(self, width: int) -> None:
        self._caret_width = max(1, min(4, int(width)))
        self.viewport().update()
        self.viewport().update()
        self._update_scrollbars()
        self.viewport().update()

    def toggle_bookmark(self) -> None:
        line = self._cursor_line
        if line in self._bookmarks:
            self._bookmarks.discard(line)
        else:
            self._bookmarks.add(line)
        self.viewport().update()

    def get_bookmarks(self) -> list[int]:
        return sorted(self._bookmarks)

    def set_bookmarks(self, lines: list[int] | set[int]) -> None:
        self._bookmarks = {int(x) for x in lines if int(x) >= 0}
        self.viewport().update()

    def next_bookmark(self) -> bool:
        if not self._bookmarks:
            return False
        after = sorted(b for b in self._bookmarks if b > self._cursor_line)
        target = after[0] if after else min(self._bookmarks)
        self.goto_line(target, 0)
        return True

    def prev_bookmark(self) -> bool:
        if not self._bookmarks:
            return False
        before = sorted(b for b in self._bookmarks if b < self._cursor_line)
        target = before[-1] if before else max(self._bookmarks)
        self.goto_line(target, 0)
        return True

    def has_bookmark(self, line: int) -> bool:
        return line in self._bookmarks

    def apply_theme_palette(self, theme_id: str) -> None:
        """Update canvas colors to match chrome theme (esp. Luminous Void)."""
        if theme_id == "luminous_void":
            self._bg = QColor(14, 14, 14)
            self._fg = QColor(229, 226, 225)
            self._line_hl = QColor(255, 215, 0, 22)
            self._sel_bg = QColor(255, 215, 0, 55)
            self._caret = QColor(255, 215, 0)
            self._gutter_fg = QColor(153, 144, 119)
            self._gutter_fg_active = QColor(255, 246, 223)
            self._bookmark_color = QColor(255, 215, 0, 220)
        elif theme_id == "clean_light":
            self._bg = QColor(255, 255, 255)
            self._fg = QColor(30, 30, 30)
            self._line_hl = QColor(37, 99, 235, 28)
            self._sel_bg = QColor(37, 99, 235, 55)
            self._caret = QColor(37, 99, 235)
            self._gutter_fg = QColor(100, 116, 139)
            self._gutter_fg_active = QColor(51, 65, 85)
            self._bookmark_color = QColor(37, 99, 235, 200)
        else:
            self._bg = QColor(15, 23, 42)
            self._fg = QColor(226, 232, 240)
            self._line_hl = QColor(56, 189, 248, 28)
            self._sel_bg = QColor(56, 189, 248, 70)
            self._caret = QColor(56, 189, 248)
            self._gutter_fg = QColor(148, 163, 184, 140)
            self._gutter_fg_active = QColor(148, 163, 184, 230)
            self._bookmark_color = QColor(56, 189, 248, 200)
        self.viewport().update()

    def zoom_in_one(self) -> None:
        f = self.font()
        f.setPointSize(min(48, f.pointSize() + 1))
        self.setFont(f)
        self._recalc_metrics()
        self.viewport().update()

    def zoom_out_one(self) -> None:
        f = self.font()
        f.setPointSize(max(8, f.pointSize() - 1))
        self.setFont(f)
        self._recalc_metrics()
        self.viewport().update()

    def reset_zoom(self) -> None:
        base = getattr(self, "_base_font_size", 12) or 12
        self.setFont(editor_font(int(base)))
        self._recalc_metrics()
        self.viewport().update()

    def find_text(
        self,
        needle: str,
        *,
        case_sensitive: bool = False,
        backward: bool = False,
        wrap: bool = True,
        use_regex: bool = False,
    ) -> bool:
        if not needle:
            return False
        try:
            pattern = compile_pattern(
                needle, case_sensitive=case_sensitive, use_regex=use_regex
            )
        except PatternError:
            return False
        self.set_find_highlight(needle, case_sensitive=case_sensitive, use_regex=use_regex)

        idx = self._doc.line_index()
        n_lines = idx.line_count
        if n_lines == 0:
            return False

        start_line = self._cursor_line
        if backward:
            order = list(range(start_line, -1, -1)) + (
                list(range(n_lines - 1, start_line, -1)) if wrap else []
            )
        else:
            order = list(range(start_line, n_lines)) + (list(range(0, start_line)) if wrap else [])

        for line in order:
            try:
                text = self._doc.line_text(line)
            except IndexError:
                continue
            if backward:
                before = self._cursor_col if line == start_line else len(text) + 1
                m = find_last_before(text, pattern, before=before)
            else:
                start_col = 0
                if line == start_line:
                    if self._cursor_col == self._last_match_start_col:
                        start_col = self._last_match_end_col
                    else:
                        start_col = self._cursor_col
                m = find_first(text, pattern, start=start_col)
            if m is None:
                continue
            self._cursor_line = line
            self._cursor_col = m.start()
            self._last_match_start_col = m.start()
            self._last_match_end_col = m.end()
            self._ensure_visible(line)
            self.cursorPositionChanged.emit()
            self.viewport().update()
            return True
        return False

    def replace_text(
        self,
        needle: str,
        replacement: str,
        *,
        case_sensitive: bool = False,
        use_regex: bool = False,
    ) -> bool:
        """Replace match at caret if it matches ``needle``, else find next and replace."""
        if not needle:
            return False
        try:
            pattern = compile_pattern(
                needle, case_sensitive=case_sensitive, use_regex=use_regex
            )
        except PatternError:
            return False
        self.set_find_highlight(needle, case_sensitive=case_sensitive, use_regex=use_regex)

        m = self._match_at_cursor_re(pattern)
        if m is None:
            if not self.find_text(
                needle,
                case_sensitive=case_sensitive,
                backward=False,
                wrap=True,
                use_regex=use_regex,
            ):
                return False
            m = self._match_at_cursor_re(pattern)
            if m is None:
                return False

        repl_text = expand_replacement(m, replacement) if use_regex else replacement
        self._replace_char_span(self._cursor_line, m.start(), m.end(), repl_text)
        return True

    def replace_all_text(
        self,
        needle: str,
        replacement: str,
        *,
        case_sensitive: bool = False,
        use_regex: bool = False,
        max_replacements: int = _MAX_REPLACE_ALL,
    ) -> int:
        """Replace all non-overlapping matches (line scan, reverse order)."""
        if not needle:
            return 0
        try:
            pattern = compile_pattern(
                needle, case_sensitive=case_sensitive, use_regex=use_regex
            )
        except PatternError:
            return 0
        self.set_find_highlight(needle, case_sensitive=case_sensitive, use_regex=use_regex)

        # (line, start_col, end_col, expanded_repl) from end of file
        jobs: list[tuple[int, int, int, str]] = []
        idx = self._doc.line_index()
        for line in range(idx.line_count - 1, -1, -1):
            try:
                text = self._doc.line_text(line)
            except IndexError:
                continue
            matches = find_all_matches(text, pattern)
            for m in reversed(matches):
                repl = expand_replacement(m, replacement) if use_regex else replacement
                jobs.append((line, m.start(), m.end(), repl))
                if len(jobs) >= max_replacements:
                    break
            if len(jobs) >= max_replacements:
                break

        count = 0
        # Apply high line first, high col first (already reverse)
        for line, start_col, end_col, repl in jobs:
            # Re-fetch line text after prior edits on same line
            try:
                self._replace_char_span(line, start_col, end_col, repl, emit=False)
            except (IndexError, ValueError):
                continue
            count += 1
        if count:
            self._cursor_line = min(self._cursor_line, self._line_count() - 1)
            self._cursor_col = min(
                self._cursor_col, len(self._doc.line_text(self._cursor_line))
            )
            self._emit_edit()
        return count

    def undo(self) -> None:
        if not self._undo:
            return
        op = self._undo.pop()
        self._applying_history = True
        try:
            if op.kind == "insert":
                self._doc.delete_bytes(op.offset, len(op.data))
                self._redo.append(op)
            else:
                self._doc.insert_bytes(op.offset, op.data)
                self._redo.append(op)
            self._place_cursor_at(op.offset)
            self._emit_edit(clear_redo=False)
        finally:
            self._applying_history = False

    def redo(self) -> None:
        if not self._redo:
            return
        op = self._redo.pop()
        self._applying_history = True
        try:
            if op.kind == "insert":
                self._doc.insert_bytes(op.offset, op.data)
                self._undo.append(op)
                self._place_cursor_at(op.offset + len(op.data))
            else:
                self._doc.delete_bytes(op.offset, len(op.data))
                self._undo.append(op)
                self._place_cursor_at(op.offset)
            self._emit_edit(clear_redo=False)
        finally:
            self._applying_history = False

    def centerCursor(self) -> None:
        self._ensure_visible(self._cursor_line)

    # --- metrics / scroll ---------------------------------------------

    def _recalc_metrics(self) -> None:
        self._line_height = max(14, self.fontMetrics().height() + 2)
        self._update_scrollbars()

    def _line_count(self) -> int:
        return max(1, self._doc.line_index().line_count)

    def _update_scrollbars(self) -> None:
        lines = self._line_count()
        visible = max(1, self.viewport().height() // self._line_height)
        self.verticalScrollBar().setRange(0, max(0, lines - 1))
        self.verticalScrollBar().setPageStep(visible)
        if self._word_wrap:
            self.horizontalScrollBar().setRange(0, 0)
        else:
            self.horizontalScrollBar().setRange(0, 200)
            self.horizontalScrollBar().setPageStep(20)

    def _text_area_width(self) -> int:
        gutter = self._gutter_width if self._show_line_numbers else 0
        return max(40, self.viewport().width() - gutter - self._pad_x * 2)

    def _wrap_display_rows(self, text: str) -> list[tuple[int, int, str]]:
        """Return (disp_start, disp_end, row_text) for expanded display string."""
        display = expand_tabs(text)
        if not self._word_wrap:
            return [(0, len(display), display)]
        fm = self.fontMetrics()
        max_w = self._text_area_width()
        ranges = wrap_ranges(display, max_w, fm.horizontalAdvance)
        return [(a, b, display[a:b]) for a, b in ranges]

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_scrollbars()

    def scrollContentsBy(self, dx: int, dy: int) -> None:
        self.viewport().scroll(dx, dy)
        self.viewport().update()

    def _ensure_visible(self, line: int) -> None:
        first = self.verticalScrollBar().value()
        visible = max(1, self.viewport().height() // self._line_height)
        if line < first:
            self.verticalScrollBar().setValue(line)
        elif line >= first + visible:
            self.verticalScrollBar().setValue(line - visible + 1)

    # --- paint --------------------------------------------------------

    def paintEvent(self, event: QPaintEvent | None) -> None:
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.viewport().rect(), self._bg)
        painter.setFont(self.font())
        fm = self.fontMetrics()
        lh = self._line_height
        first = self.verticalScrollBar().value()
        space_w = fm.horizontalAdvance(" ")
        h_off = 0 if self._word_wrap else self.horizontalScrollBar().value() * space_w
        gutter = self._gutter_width if self._show_line_numbers else 0
        total = self._line_count()
        do_syntax = (
            self._syntax_enabled
            and self._language not in {"", "text"}
            and not self._word_wrap
        )
        view_h = self.viewport().height()

        if gutter:
            painter.fillRect(0, 0, gutter, view_h, self._gutter_bg)

        y = 0
        line = first
        while y < view_h and line < total:
            try:
                text = self._doc.line_text(line)
            except IndexError:
                text = ""
            rows = self._wrap_display_rows(text)
            row_h = lh * len(rows)
            if line == self._cursor_line and self._highlight_current_line:
                painter.fillRect(
                    gutter,
                    y,
                    self.viewport().width() - gutter,
                    row_h,
                    self._line_hl,
                )
            if gutter:
                if line in self._bookmarks:
                    painter.setBrush(self._bookmark_color)
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawEllipse(4, y + lh // 2 - 4, 8, 8)
                num = str(line + 1)
                painter.setPen(
                    self._gutter_fg_active if line == self._cursor_line else self._gutter_fg
                )
                painter.drawText(
                    0,
                    y,
                    gutter - 8,
                    lh,
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                    num,
                )

            base_x = gutter + self._pad_x - h_off
            sel_cols = self._selection_cols_on_line(line)
            for ri, (d0, d1, row) in enumerate(rows):
                ry = y + ri * lh
                if ry > view_h:
                    break
                baseline = ry + fm.ascent() + 1
                if sel_cols is not None:
                    self._paint_selection_row(
                        painter, text, sel_cols, d0, d1, base_x, ry, lh, fm
                    )
                if self._find_needle:
                    self._paint_find_hits_row(painter, text, d0, d1, base_x, ry, lh, fm)
                # Spell: only current painted line (viewport-safe for huge files)
                if self._spell is not None and text and len(text) <= 4000:
                    self._paint_spell_row(painter, text, d0, d1, base_x, ry, lh, fm)
                if do_syntax and text and len(text) <= 8000 and not self._word_wrap:
                    self._paint_syntax_line(painter, text, row, base_x, baseline, fm)
                else:
                    painter.setPen(self._fg)
                    painter.drawText(base_x, baseline, row)
                if self._show_whitespace and row:
                    self._paint_whitespace(painter, row, base_x, ry, lh, fm)
                # Brace match underline
                if (
                    self._brace_match_enabled
                    and self._brace_match_col is not None
                    and self._brace_line == line
                    and d0 <= self._brace_match_col < d1
                ):
                    self._paint_brace_mark(
                        painter, text, self._brace_match_col, d0, base_x, ry, lh, fm
                    )
                if (
                    self._brace_match_enabled
                    and self._brace_pair_col is not None
                    and self._brace_pair_line == line
                    and d0 <= self._brace_pair_col < d1
                ):
                    self._paint_brace_mark(
                        painter, text, self._brace_pair_col, d0, base_x, ry, lh, fm
                    )

                if line == self._cursor_line:
                    caret_disp = len(expand_tabs(text[: self._cursor_col]))
                    if d0 <= caret_disp <= d1:
                        prefix = row[: caret_disp - d0]
                        cx = base_x + fm.horizontalAdvance(prefix)
                        painter.setPen(self._caret)
                        for dx in range(self._caret_width):
                            painter.drawLine(
                                cx + dx, ry + 1, cx + dx, ry + lh - 2
                            )
                # Extra multi-carets
                for el, esc, eec in self._extra_cursors:
                    if el != line:
                        continue
                    caret_disp = len(expand_tabs(text[:esc]))
                    if d0 <= caret_disp <= d1:
                        prefix = row[: caret_disp - d0]
                        cx = base_x + fm.horizontalAdvance(prefix)
                        painter.setPen(self._caret)
                        painter.drawLine(cx, ry + 1, cx, ry + lh - 2)
                    if esc != eec:
                        self._paint_selection_row(
                            painter, text, (esc, eec), d0, d1, base_x, ry, lh, fm
                        )

            y += row_h
            line += 1

    def _paint_selection_row(
        self,
        painter: QPainter,
        text: str,
        sel_cols: tuple[int, int],
        d0: int,
        d1: int,
        base_x: int,
        y: int,
        lh: int,
        fm,
    ) -> None:
        a_col, b_col = sel_cols
        md0 = len(expand_tabs(text[:a_col]))
        md1 = len(expand_tabs(text[:b_col]))
        if md1 <= d0 or md0 >= d1:
            return
        a = max(md0, d0) - d0
        b = min(md1, d1) - d0
        row = expand_tabs(text)[d0:d1]
        x0 = base_x + fm.horizontalAdvance(row[:a])
        w = fm.horizontalAdvance(row[a:b])
        painter.fillRect(x0, y + 1, max(2, w), lh - 2, self._sel_bg)

    def _paint_whitespace(
        self, painter: QPainter, row: str, base_x: int, ry: int, lh: int, fm
    ) -> None:
        """Subtle mid-dots for spaces and » for tabs in the display row."""
        dim = QColor(self._gutter_fg)
        dim.setAlpha(110)
        painter.setPen(dim)
        x = base_x
        for ch in row:
            w = fm.horizontalAdvance(ch)
            if ch == " ":
                painter.drawText(x, ry + lh - 4, "·")
            elif ch == "\t":
                painter.drawText(x, ry + lh - 4, "»")
            x += w

    def _paint_spell_row(
        self,
        painter: QPainter,
        text: str,
        d0: int,
        d1: int,
        base_x: int,
        ry: int,
        lh: int,
        fm,
    ) -> None:
        if self._spell is None:
            return
        # Map display cols to approx char cols for non-wrap path
        for hit in self._spell.check_text(text):
            if hit.end <= d0 or hit.start >= d1:
                continue
            a = max(hit.start, d0)
            b = min(hit.end, d1)
            if d0 == 0:
                x0 = base_x + fm.horizontalAdvance(expand_tabs(text[:a]))
            else:
                x0 = base_x + fm.horizontalAdvance(
                    expand_tabs(text[d0:a]) if a >= d0 else ""
                )
            w = max(2, fm.horizontalAdvance(expand_tabs(text[a:b])))
            painter.setPen(self._spell_color)
            y_line = ry + lh - 2
            # Squiggle-style underline (more visible than a hairline)
            x = x0
            amp = 2
            while x < x0 + w:
                x2 = min(x + 3, x0 + w)
                painter.drawLine(int(x), y_line + amp, int(x2), y_line - amp)
                x = x2
                amp = -amp

    def _paint_brace_mark(
        self,
        painter: QPainter,
        text: str,
        col: int,
        d0: int,
        base_x: int,
        ry: int,
        lh: int,
        fm,
    ) -> None:
        if col < d0:
            return
        x0 = base_x + fm.horizontalAdvance(expand_tabs(text[d0:col]))
        w = fm.horizontalAdvance(text[col : col + 1] if col < len(text) else " ")
        painter.fillRect(x0, ry + lh - 3, max(2, w), 2, QColor(255, 215, 0, 200))

    def _paint_find_hits_row(
        self,
        painter: QPainter,
        text: str,
        d0: int,
        d1: int,
        base_x: int,
        y: int,
        lh: int,
        fm,
    ) -> None:
        needle = self._find_needle
        if not needle or not text:
            return
        try:
            pattern = compile_pattern(
                needle,
                case_sensitive=self._find_case,
                use_regex=self._find_regex,
            )
        except PatternError:
            return
        for m in find_all_matches(text, pattern):
            md0 = len(expand_tabs(text[: m.start()]))
            md1 = len(expand_tabs(text[: m.end()]))
            if md1 <= d0 or md0 >= d1:
                continue
            a = max(md0, d0) - d0
            b = min(md1, d1) - d0
            row = expand_tabs(text)[d0:d1]
            x0 = base_x + fm.horizontalAdvance(row[:a])
            w = fm.horizontalAdvance(row[a:b])
            painter.fillRect(x0, y + 1, max(1, w), lh - 2, _FIND_BG)

    def _paint_syntax_line(
        self,
        painter: QPainter,
        text: str,
        display: str,
        base_x: int,
        baseline: int,
        fm,
    ) -> None:
        """Paint a line with per-token colors (visible range only)."""
        spans = tokenize_line(text, self._language)
        claimed_end = 0
        x = base_x
        bold_font = QFont(self.font())
        bold_font.setBold(True)
        normal_font = self.font()

        def expand_slice(start: int, end: int) -> str:
            return text[start:end].replace("\t", "    ")

        for start, length, kind in spans:
            if start > claimed_end:
                gap = expand_slice(claimed_end, start)
                painter.setFont(normal_font)
                painter.setPen(QColor(_DEFAULT_FG))
                painter.drawText(x, baseline, gap)
                x += fm.horizontalAdvance(gap)
            chunk = expand_slice(start, start + length)
            color, bold = _SYNTAX_PALETTE.get(kind, (_DEFAULT_FG, False))
            painter.setFont(bold_font if bold else normal_font)
            painter.setPen(QColor(color))
            painter.drawText(x, baseline, chunk)
            x += fm.horizontalAdvance(chunk)
            claimed_end = start + length

        if claimed_end < len(text):
            tail = expand_slice(claimed_end, len(text))
            painter.setFont(normal_font)
            painter.setPen(QColor(_DEFAULT_FG))
            painter.drawText(x, baseline, tail)
        elif not spans:
            painter.setFont(normal_font)
            painter.setPen(QColor(_DEFAULT_FG))
            painter.drawText(base_x, baseline, display)

        painter.setFont(self.font())

    # --- input --------------------------------------------------------

    def wheelEvent(self, event: QWheelEvent | None) -> None:
        if event is None:
            return
        delta = event.angleDelta().y()
        step = -3 if delta > 0 else 3
        sb = self.verticalScrollBar()
        sb.setValue(sb.value() + step)
        event.accept()

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        if event is None:
            return
        key = event.key()
        mod = event.modifiers()
        lines = self._line_count()
        visible = max(1, self.viewport().height() // self._line_height)
        ctrl = bool(mod & Qt.KeyboardModifier.ControlModifier)
        shift = bool(mod & Qt.KeyboardModifier.ShiftModifier)

        if ctrl and key == Qt.Key.Key_Z and not shift:
            self.undo()
            event.accept()
            return
        if ctrl and (key == Qt.Key.Key_Y or (key == Qt.Key.Key_Z and shift)):
            self.redo()
            event.accept()
            return
        # Clipboard (Ctrl+C/X/V/A) is owned by MainWindow QActions.

        nav_keys = {
            Qt.Key.Key_Up,
            Qt.Key.Key_Down,
            Qt.Key.Key_PageUp,
            Qt.Key.Key_PageDown,
            Qt.Key.Key_Home,
            Qt.Key.Key_End,
            Qt.Key.Key_Left,
            Qt.Key.Key_Right,
        }
        if key in nav_keys:
            self._begin_selection_if_needed(shift)

        if key == Qt.Key.Key_Up:
            self._cursor_line = max(0, self._cursor_line - 1)
        elif key == Qt.Key.Key_Down:
            self._cursor_line = min(lines - 1, self._cursor_line + 1)
        elif key == Qt.Key.Key_PageUp:
            self._cursor_line = max(0, self._cursor_line - visible)
        elif key == Qt.Key.Key_PageDown:
            self._cursor_line = min(lines - 1, self._cursor_line + visible)
        elif key == Qt.Key.Key_Home:
            self._cursor_col = 0
        elif key == Qt.Key.Key_End:
            self._cursor_col = len(self._doc.line_text(self._cursor_line))
        elif key == Qt.Key.Key_Left:
            self._cursor_col = max(0, self._cursor_col - 1)
        elif key == Qt.Key.Key_Right:
            self._cursor_col = min(
                len(self._doc.line_text(self._cursor_line)), self._cursor_col + 1
            )
        elif key == Qt.Key.Key_Tab and not ctrl:
            if self._try_snippet_or_complete():
                event.accept()
                self._ensure_visible(self._cursor_line)
                self._update_brace_match()
                self.cursorPositionChanged.emit()
                self.viewport().update()
                return
            # default indent
            self.indent_line()
            event.accept()
            self.viewport().update()
            return
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            # Multi-cursor/column newline: stream-delete only for plain selection
            if self._multi_edit_spans():
                # insert path handles multi spans for non-newline only;
                # for newline, apply stream delete of multi zero-width not supported —
                # clear multi and insert single newline at primary after deleting spans
                if self.has_selection() or self._extra_cursors:
                    self._delete_selection(emit=False)
                self._insert_at_cursor("\n")
            else:
                if self.has_selection():
                    self._delete_selection(emit=False)
                self._insert_at_cursor("\n")
        elif key == Qt.Key.Key_Backspace:
            self._backspace()
        elif key == Qt.Key.Key_Delete:
            self._delete_forward()
        elif event.text() and not ctrl:
            # CRITICAL: do NOT call _delete_selection before multi/column insert —
            # that clears _extra_cursors / _column_mode. _insert_at_cursor replaces
            # each multi-edit span itself (including zero-width carets).
            if self._multi_edit_spans():
                self._insert_at_cursor(event.text())
            else:
                if self.has_selection():
                    self._delete_selection(emit=False)
                self._insert_at_cursor(event.text())
            if self._word_completion and event.text().isalnum():
                self._refresh_completion_candidates()
        else:
            super().keyPressEvent(event)
            return

        self._ensure_visible(self._cursor_line)
        self._update_brace_match()
        self.cursorPositionChanged.emit()
        self.viewport().update()
        event.accept()

    def mousePressEvent(self, event) -> None:
        if event is None:
            return
        # Right-click: request context menu (primary path for QAbstractScrollArea)
        if event.button() == Qt.MouseButton.RightButton:
            self.setFocus(Qt.FocusReason.MouseFocusReason)
            global_pos = event.globalPosition().toPoint()
            self._context_menu_from_mouse = True
            self._emit_context_menu(global_pos)
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            pos: QPoint = event.position().toPoint()
            line, col = self._hit_test(pos)
            shift = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
            alt = bool(event.modifiers() & Qt.KeyboardModifier.AltModifier)
            ctrl = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
            if alt:
                # Column / block selection start
                self._column_mode = True
                self._column_anchor = (line, col)
                self._extra_cursors.clear()
                self._anchor_line = line
                self._anchor_col = col
                self._cursor_line = line
                self._cursor_col = col
                self._selecting = True
            elif ctrl:
                # Ctrl+click multi-cursor
                self._extra_cursors.append((line, col, col))
                self._cursor_line = line
                self._cursor_col = col
            elif shift:
                if self._anchor_line is None:
                    self._anchor_line = self._cursor_line
                    self._anchor_col = self._cursor_col
                self._cursor_line = line
                self._cursor_col = col
            else:
                self._column_mode = False
                self._column_anchor = None
                self._extra_cursors.clear()
                self._anchor_line = line
                self._anchor_col = col
                self._cursor_line = line
                self._cursor_col = col
            self._selecting = True
            self._update_brace_match()
            self.cursorPositionChanged.emit()
            self.viewport().update()
            self.setFocus()
            event.accept()
            return
        super().mousePressEvent(event)

    def contextMenuEvent(self, event: QContextMenuEvent | None) -> None:
        """Keyboard context menu (Shift+F10 / menu key); skip if mouse already opened it."""
        if event is None:
            return
        if not self._context_menu_enabled:
            event.ignore()
            return
        # Avoid double-open after right-button mousePress
        if self._context_menu_from_mouse:
            self._context_menu_from_mouse = False
            event.accept()
            return
        self._emit_context_menu(event.globalPos())
        event.accept()

    def viewportEvent(self, event: QEvent | None) -> bool:
        """Route viewport mouse / context events into VirtualEditor handlers."""
        if event is None:
            return False
        et = event.type()
        if et == QEvent.Type.MouseButtonPress:
            self.mousePressEvent(event)  # type: ignore[arg-type]
            return event.isAccepted() or super().viewportEvent(event)
        if et == QEvent.Type.MouseMove:
            self.mouseMoveEvent(event)  # type: ignore[arg-type]
            return event.isAccepted() or super().viewportEvent(event)
        if et == QEvent.Type.MouseButtonRelease:
            self.mouseReleaseEvent(event)  # type: ignore[arg-type]
            return event.isAccepted() or super().viewportEvent(event)
        if et == QEvent.Type.ContextMenu:
            self.contextMenuEvent(event)  # type: ignore[arg-type]
            return True
        return super().viewportEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._selecting and event is not None and (
            event.buttons() & Qt.MouseButton.LeftButton
        ):
            pos: QPoint = event.position().toPoint()
            line, col = self._hit_test(pos)
            self._cursor_line = line
            self._cursor_col = col
            # Keep column mode active while Alt held or already in column drag
            if self._column_mode and self._column_anchor is not None:
                self._anchor_line = self._column_anchor[0]
                self._anchor_col = self._column_anchor[1]
            self.cursorPositionChanged.emit()
            self.viewport().update()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event is not None and event.button() == Qt.MouseButton.LeftButton:
            self._selecting = False
            # Click without drag → caret only (no selection)
            if (
                self._anchor_line is not None
                and self._anchor_line == self._cursor_line
                and self._anchor_col == self._cursor_col
            ):
                self._clear_selection()
            event.accept()
        super().mouseReleaseEvent(event)

    def _hit_test(self, pos: QPoint) -> tuple[int, int]:
        """Map viewport point to (doc_line, char_col)."""
        first = self.verticalScrollBar().value()
        lh = self._line_height
        gutter = self._gutter_width if self._show_line_numbers else 0
        fm = self.fontMetrics()
        space_w = fm.horizontalAdvance(" ")
        h_off = 0 if self._word_wrap else self.horizontalScrollBar().value() * space_w
        x = pos.x() - gutter - self._pad_x + h_off
        y = 0
        total = self._line_count()
        line = first
        while line < total:
            try:
                text = self._doc.line_text(line)
            except IndexError:
                text = ""
            rows = self._wrap_display_rows(text)
            for d0, _d1, row in rows:
                if y <= pos.y() < y + lh:
                    col_disp = 0
                    acc = 0
                    for ch in row:
                        w = fm.horizontalAdvance(ch)
                        if acc + w / 2 >= x:
                            break
                        acc += w
                        col_disp += 1
                    target_disp = d0 + col_disp
                    # Map expanded display index back to text column
                    col = 0
                    disp = 0
                    for ch in text:
                        step = 4 if ch == "\t" else 1
                        if disp + step > target_disp:
                            break
                        disp += step
                        col += 1
                    return line, col
                y += lh
            line += 1
        return max(0, total - 1), 0

    # --- edits (piece table + incremental line index + undo) ----------

    def _byte_offset_at_cursor(self) -> int:
        idx = self._doc.line_index()
        start = idx.line_start(self._cursor_line)
        return start + self._col_to_byte(self._cursor_line, self._cursor_col)

    def _col_to_byte(self, line: int, col: int) -> int:
        text = self._doc.line_text(line)
        prefix = text[:col]
        enc = self._doc.encoding if self._doc.encoding != "utf-8-sig" else "utf-8"
        return len(prefix.encode(enc, errors="replace"))

    def _byte_to_col(self, line: int, byte_off: int) -> int:
        text = self._doc.line_text(line)
        enc = self._doc.encoding if self._doc.encoding != "utf-8-sig" else "utf-8"
        raw = text.encode(enc, errors="replace")
        used = 0
        col = 0
        for ch in text:
            b = ch.encode(enc, errors="replace")
            if used + len(b) > byte_off:
                break
            used += len(b)
            col += 1
            if used >= len(raw):
                break
        return col

    def _match_at_cursor_re(self, pattern) -> object | None:
        """Return re.Match if a match starts at the caret column."""
        text = self._doc.line_text(self._cursor_line)
        m = pattern.match(text, self._cursor_col)
        return m

    def _replace_char_span(
        self,
        line: int,
        start_col: int,
        end_col: int,
        replacement: str,
        *,
        emit: bool = True,
    ) -> None:
        """Replace character range on a line via byte offsets."""
        enc = self._doc.encoding if self._doc.encoding != "utf-8-sig" else "utf-8"
        line_start = self._doc.line_index().line_start(line)
        off = line_start + self._col_to_byte(line, start_col)
        end_off = line_start + self._col_to_byte(line, end_col)
        if end_off > off:
            self._delete_bytes_tracked(off, end_off - off)
        repl_b = replacement.encode(enc, errors="replace")
        if repl_b:
            self._insert_bytes_tracked(off, repl_b)
        if emit:
            self._place_cursor_at(off + len(repl_b))
            self._last_match_start_col = -1
            self._last_match_end_col = 0
            self._emit_edit()

    def _push_undo(self, op: _EditOp) -> None:
        if self._applying_history:
            return
        self._undo.append(op)
        if len(self._undo) > _MAX_UNDO:
            self._undo = self._undo[-_MAX_UNDO:]
        self._redo.clear()

    def _insert_bytes_tracked(self, offset: int, data: bytes) -> None:
        if not data:
            return
        self._doc.insert_bytes(offset, data)
        self._push_undo(_EditOp("insert", offset, data))

    def _delete_bytes_tracked(self, offset: int, length: int) -> None:
        if length <= 0:
            return
        deleted = self._doc.buffer.get_text(offset, length)
        self._doc.delete_bytes(offset, length)
        self._push_undo(_EditOp("delete", offset, deleted))

    def _place_cursor_at(self, byte_off: int) -> None:
        byte_off = max(0, min(len(self._doc.buffer), byte_off))
        self._cursor_line = self._doc.line_index().offset_to_line(byte_off)
        line_start = self._doc.line_index().line_start(self._cursor_line)
        self._cursor_col = self._byte_to_col(self._cursor_line, byte_off - line_start)

    def _emit_edit(self, *, clear_redo: bool = True) -> None:
        if clear_redo and not self._applying_history:
            pass  # redo already cleared in _push_undo
        self._modified = True
        self._update_scrollbars()
        self.textChanged.emit()
        self.modificationChanged.emit(True)
        self.cursorPositionChanged.emit()
        self.viewport().update()

    def _insert_at_cursor(self, text: str) -> None:
        enc = self._doc.encoding if self._doc.encoding != "utf-8-sig" else "utf-8"
        data = text.encode(enc, errors="replace")
        spans = self._multi_edit_spans()
        if spans and not (b"\n" in data or b"\r" in data):
            # multi-cursor / column insert (same text at each span end)
            was_column = self._column_mode
            post_carets: list[tuple[int, int]] = []
            for line, c0, c1 in spans:
                line_text = self._doc.line_text(line)
                # pad line with spaces if column beyond EOL
                if c0 > len(line_text):
                    pad = c0 - len(line_text)
                    pad_off = (
                        self._doc.line_index().line_start(line)
                        + self._col_to_byte(line, len(line_text))
                    )
                    self._insert_bytes_tracked(pad_off, b" " * pad)
                    line_text = self._doc.line_text(line)
                a = min(c0, len(line_text))
                b = min(max(c1, c0), len(self._doc.line_text(line)))
                start = self._doc.line_index().line_start(line) + self._col_to_byte(line, a)
                if b > a:
                    end = self._doc.line_index().line_start(line) + self._col_to_byte(
                        line, b
                    )
                    self._delete_bytes_tracked(start, end - start)
                self._insert_bytes_tracked(start, data)
                new_col = a + len(text)
                post_carets.append((line, new_col))
            # Single restore path: N carets in → N carets out (no drop/dupe)
            primary, extras = restore_carets_after_multi_insert(post_carets)
            self._cursor_line, self._cursor_col = primary
            self._extra_cursors = list(extras)
            self._clear_selection()
            if was_column and len(post_carets) > 1:
                # Keep column mode for next keystroke; anchor = topmost caret
                sorted_carets = sorted(post_carets, key=lambda t: (t[0], t[1]))
                self._column_mode = True
                self._column_anchor = sorted_carets[0]
                self._anchor_line = sorted_carets[0][0]
                self._anchor_col = sorted_carets[0][1]
            else:
                self._column_mode = False
                self._column_anchor = None
            self._emit_edit()
            return

        off = self._byte_offset_at_cursor()
        self._insert_bytes_tracked(off, data)
        self._clear_selection()
        self._extra_cursors.clear()
        self._column_mode = False
        self._column_anchor = None
        if b"\n" in data or b"\r" in data:
            self._cursor_line = self._doc.line_index().offset_to_line(off + len(data))
            line_start = self._doc.line_index().line_start(self._cursor_line)
            self._cursor_col = self._byte_to_col(
                self._cursor_line, off + len(data) - line_start
            )
        else:
            self._cursor_col += len(text)
        self._emit_edit()

    def _backspace(self) -> None:
        if self.has_selection() or self._extra_cursors or self._column_rect():
            # if zero-width multi carets, delete one char left at each
            spans = self._multi_edit_spans()
            if spans and all(c0 == c1 for _, c0, c1 in spans):
                for line, c0, _c1 in spans:
                    if c0 <= 0:
                        continue
                    start = self._doc.line_index().line_start(line) + self._col_to_byte(
                        line, c0 - 1
                    )
                    end = self._doc.line_index().line_start(line) + self._col_to_byte(
                        line, c0
                    )
                    if end > start:
                        self._delete_bytes_tracked(start, end - start)
                # rebuild carets
                rebuilt = [(ln, max(0, c0 - 1), max(0, c0 - 1)) for ln, c0, _ in spans]
                rebuilt.sort(key=lambda t: (t[0], t[1]))
                if rebuilt:
                    self._cursor_line, self._cursor_col, _ = rebuilt[-1]
                    self._extra_cursors = [
                        (ln, c, c) for ln, c, _ in rebuilt[:-1]
                    ]
                self._clear_selection()
                self._emit_edit()
                return
            self._delete_selection()
            return
        off = self._byte_offset_at_cursor()
        if off <= 0:
            return
        self._delete_bytes_tracked(off - 1, 1)
        self._place_cursor_at(off - 1)
        self._emit_edit()

    def _delete_forward(self) -> None:
        if self.has_selection() or self._extra_cursors or self._column_rect():
            spans = self._multi_edit_spans()
            if spans and all(c0 == c1 for _, c0, c1 in spans):
                for line, c0, _c1 in spans:
                    text = self._doc.line_text(line)
                    if c0 >= len(text):
                        continue
                    start = self._doc.line_index().line_start(line) + self._col_to_byte(
                        line, c0
                    )
                    end = self._doc.line_index().line_start(line) + self._col_to_byte(
                        line, c0 + 1
                    )
                    if end > start:
                        self._delete_bytes_tracked(start, end - start)
                self._emit_edit()
                return
            self._delete_selection()
            return
        off = self._byte_offset_at_cursor()
        if off >= len(self._doc.buffer):
            return
        self._delete_bytes_tracked(off, 1)
        self._emit_edit()

    def _try_snippet_or_complete(self) -> bool:
        """Tab: expand snippet trigger or word-complete. Returns True if handled."""
        if self.has_selection() or self._extra_cursors:
            return False
        line_text = self._doc.line_text(self._cursor_line)
        col = self._cursor_col
        # word prefix before cursor
        i = col
        while i > 0 and (line_text[i - 1].isalnum() or line_text[i - 1] in {"_", "$"}):
            i -= 1
        prefix = line_text[i:col]
        if not prefix:
            return False
        sn = match_trigger(prefix, self._language)
        if sn is not None and (prefix == sn.trigger or prefix.endswith(sn.trigger)):
            # replace trigger with body
            body, caret = expand_snippet(sn.body)
            start_col = col - len(sn.trigger) if prefix.endswith(sn.trigger) else i
            # if prefix == trigger use i
            if prefix == sn.trigger:
                start_col = i
            else:
                start_col = col - len(sn.trigger)
            start = self._doc.line_index().line_start(self._cursor_line) + self._col_to_byte(
                self._cursor_line, start_col
            )
            end = self._doc.line_index().line_start(self._cursor_line) + self._col_to_byte(
                self._cursor_line, col
            )
            if end > start:
                self._delete_bytes_tracked(start, end - start)
            enc = self._doc.encoding if self._doc.encoding != "utf-8-sig" else "utf-8"
            data = body.encode(enc, errors="replace")
            self._insert_bytes_tracked(start, data)
            # place cursor: prefer $0 offset within expanded body
            self._place_cursor_at(start + len(body[:caret].encode(enc, errors="replace")))
            self._emit_edit()
            return True
        if self._word_completion:
            return self._apply_word_completion(prefix, i, col)
        return False

    def _refresh_completion_candidates(self) -> None:
        line_text = self._doc.line_text(self._cursor_line)
        w = word_at([line_text], 0, self._cursor_col)
        if w is None:
            self._completion_candidates = []
            return
        word, _start, _end = w
        prefix = word
        if not prefix:
            self._completion_candidates = []
            return
        # build vocabulary from nearby lines (viewport-ish, capped)
        total = self._line_count()
        lo = max(0, self._cursor_line - 200)
        hi = min(total, self._cursor_line + 200)
        found: set[str] = set()
        for ln in range(lo, hi):
            t = self._doc.line_text(ln)
            for part in t.replace(",", " ").replace(".", " ").split():
                token = "".join(ch for ch in part if ch.isalnum() or ch == "_")
                if len(token) > len(prefix) and token.startswith(prefix):
                    found.add(token)
        self._completion_candidates = sorted(found)[:40]
        self._completion_index = 0

    def _apply_word_completion(self, prefix: str, start_col: int, end_col: int) -> bool:
        self._refresh_completion_candidates()
        if not self._completion_candidates:
            return False
        choice = self._completion_candidates[
            self._completion_index % len(self._completion_candidates)
        ]
        self._completion_index += 1
        start = self._doc.line_index().line_start(self._cursor_line) + self._col_to_byte(
            self._cursor_line, start_col
        )
        end = self._doc.line_index().line_start(self._cursor_line) + self._col_to_byte(
            self._cursor_line, end_col
        )
        if end > start:
            self._delete_bytes_tracked(start, end - start)
        enc = self._doc.encoding if self._doc.encoding != "utf-8-sig" else "utf-8"
        data = choice.encode(enc, errors="replace")
        self._insert_bytes_tracked(start, data)
        self._cursor_col = start_col + len(choice)
        self._emit_edit()
        return True

    def cursor_line_col(self) -> tuple[int, int]:
        return self._cursor_line + 1, self._cursor_col + 1

    def indent_line(self) -> None:
        """Insert tab or N spaces at the start of the current line."""
        start = self._doc.line_index().line_start(self._cursor_line)
        if self._indent_with_spaces:
            n = max(2, min(8, self._tab_width))
            chunk = b" " * n
            self._insert_bytes_tracked(start, chunk)
            self._cursor_col += n
        else:
            self._insert_bytes_tracked(start, b"\t")
            self._cursor_col += 1
        self._clear_selection()
        self._emit_edit()

    def unindent_line(self) -> None:
        text = self._doc.line_text(self._cursor_line)
        strip = 0
        n = max(2, min(8, self._tab_width))
        if text.startswith("\t"):
            strip = 1
        elif text.startswith(" " * n):
            strip = n
        elif text.startswith(" "):
            strip = min(n, len(text) - len(text.lstrip(" ")))
        if strip <= 0:
            return
        start = self._doc.line_index().line_start(self._cursor_line)
        self._delete_bytes_tracked(start, self._col_to_byte(self._cursor_line, strip))
        self._cursor_col = max(0, self._cursor_col - strip)
        self._clear_selection()
        self._emit_edit()

    def duplicate_line(self) -> None:
        text = self._doc.line_text(self._cursor_line)
        enc = self._doc.encoding if self._doc.encoding != "utf-8-sig" else "utf-8"
        line = self._cursor_line
        total = self._line_count()
        if line < total - 1:
            off = self._doc.line_index().line_start(line + 1)
            data = (text + "\n").encode(enc, errors="replace")
        else:
            off = len(self._doc.buffer)
            data = ("\n" + text).encode(enc, errors="replace")
        self._insert_bytes_tracked(off, data)
        self._clear_selection()
        self._emit_edit()
