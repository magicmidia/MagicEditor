"""Virtual viewport editor — paints only visible lines from a piece table."""

from __future__ import annotations

from PyQt6.QtCore import QEvent, QPoint, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QContextMenuEvent, QKeyEvent, QPaintEvent, QWheelEvent
from PyQt6.QtWidgets import QAbstractScrollArea, QWidget

from magiceditor.core.spell import SpellEngine
from magiceditor.services.document import Document
from magiceditor.ui.fonts import editor_font
from magiceditor.ui.syntax_cache import LineTokenCache
from magiceditor.ui.virtual_chrome import (
    apply_brace_enabled,
    update_brace_match,
)
from magiceditor.ui.virtual_chrome import (
    apply_theme_palette as chrome_apply_theme,
)
from magiceditor.ui.virtual_chrome import (
    next_bookmark as chrome_next_bookmark,
)
from magiceditor.ui.virtual_chrome import (
    prev_bookmark as chrome_prev_bookmark,
)
from magiceditor.ui.virtual_chrome import (
    set_font_point_size as chrome_set_font,
)
from magiceditor.ui.virtual_chrome import (
    toggle_bookmark as chrome_toggle_bookmark,
)
from magiceditor.ui.virtual_chrome import (
    zoom_in as chrome_zoom_in,
)
from magiceditor.ui.virtual_chrome import (
    zoom_out as chrome_zoom_out,
)
from magiceditor.ui.virtual_chrome import (
    zoom_reset as chrome_zoom_reset,
)
from magiceditor.ui.virtual_clipboard import (
    begin_selection_if_needed as clip_begin_sel,
)
from magiceditor.ui.virtual_clipboard import (
    clear_selection as clip_clear,
)
from magiceditor.ui.virtual_clipboard import (
    copy_selection as clip_copy,
)
from magiceditor.ui.virtual_clipboard import (
    cut_selection as clip_cut,
)
from magiceditor.ui.virtual_clipboard import (
    delete_selection as clip_delete,
)
from magiceditor.ui.virtual_clipboard import (
    editor_normalized_selection as clip_norm,
)
from magiceditor.ui.virtual_clipboard import (
    has_selection as clip_has,
)
from magiceditor.ui.virtual_clipboard import (
    paste_clipboard as clip_paste,
)
from magiceditor.ui.virtual_clipboard import (
    replace_word_on_line as clip_replace_word,
)
from magiceditor.ui.virtual_clipboard import (
    select_all as clip_select_all,
)
from magiceditor.ui.virtual_clipboard import (
    selected_text as clip_selected,
)
from magiceditor.ui.virtual_clipboard import (
    selection_cols_on_line as clip_cols,
)
from magiceditor.ui.virtual_cursors import (
    backspace as cursors_backspace,
)
from magiceditor.ui.virtual_cursors import (
    delete_forward as cursors_delete_forward,
)
from magiceditor.ui.virtual_cursors import (
    editor_column_rect,
    editor_multi_spans,
)
from magiceditor.ui.virtual_edit import (
    byte_offset_at_cursor as edit_byte_offset,
)
from magiceditor.ui.virtual_edit import (
    editor_byte_to_col,
    editor_col_to_byte,
    emit_edit,
    export_editor_text,
    insert_at_cursor,
    place_cursor_at,
)
from magiceditor.ui.virtual_find import (
    MAX_REPLACE_ALL,
    find_in_editor,
    replace_all_in_editor,
    replace_char_span,
    replace_in_editor,
)
from magiceditor.ui.virtual_keys import (
    handle_key_press,
    intercept_tab_event,
    newline_for_editor,
    try_snippet_or_complete,
)
from magiceditor.ui.virtual_keys import (
    indent_line as keys_indent_line,
)
from magiceditor.ui.virtual_keys import (
    unindent_line as keys_unindent_line,
)
from magiceditor.ui.virtual_metrics import (
    ensure_visible as metrics_ensure_visible,
)
from magiceditor.ui.virtual_metrics import (
    line_count as metrics_line_count,
)
from magiceditor.ui.virtual_metrics import (
    recalc_metrics as metrics_recalc,
)
from magiceditor.ui.virtual_metrics import (
    update_scrollbars as metrics_scrollbars,
)
from magiceditor.ui.virtual_metrics import (
    wrap_display_rows as metrics_wrap,
)
from magiceditor.ui.virtual_mouse import (
    handle_context_menu,
    handle_mouse_move,
    handle_mouse_press,
    handle_mouse_release,
    handle_viewport_event,
    handle_wheel,
    hit_test,
)
from magiceditor.ui.virtual_paint import paint_event as paint_viewport
from magiceditor.ui.virtual_spell import refresh_visible_spans
from magiceditor.ui.virtual_undo import (
    UndoHistory,
    redo_editor,
    track_delete,
    track_insert,
    undo_editor,
)


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
        self._syntax_light = False
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
        self._history = UndoHistory()
        # Multi-cursor: list of (line, start_col, end_col)
        self._extra_cursors: list[tuple[int, int, int]] = []
        # Column (block) selection mode
        self._column_mode = False
        self._column_anchor: tuple[int, int] | None = None
        # Auto-scroll while drag-selecting past the viewport edge
        self._auto_scroll_dy = 0
        self._auto_scroll_pos: QPoint | None = None
        self._auto_scroll_timer: QTimer | None = None
        # Spell (viewport only) — spans computed off paint (K3)
        self._spell: SpellEngine | None = None
        self._spell_color = QColor(239, 68, 68, 220)
        self._spell_spans: dict[int, tuple[tuple[int, int], ...]] = {}
        self._token_cache = LineTokenCache()
        self._antialiasing = True
        self._spell_debounce = QTimer(self)
        self._spell_debounce.setSingleShot(True)
        self._spell_debounce.setInterval(60)
        self._spell_debounce.timeout.connect(self._refresh_spell_spans)
        self.textChanged.connect(self._on_buffer_changed)
        self.verticalScrollBar().valueChanged.connect(self._schedule_spell_refresh)
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
        self.viewport().setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFrameShape(self.Shape.NoFrame)
        self.viewport().setCursor(Qt.CursorShape.IBeamCursor)
        # Context menu: QAbstractScrollArea delivers ContextMenu to this widget
        # via viewportEvent — policy on both self and viewport for reliability.
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)
        self.viewport().setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)
        self.setViewportMargins(0, 0, 0, 0)
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
            self.viewport().update()
            return
        self._language = language
        self.viewport().update()

    def language(self) -> str:
        return self._language

    def set_syntax_light_theme(self, light: bool) -> None:
        self._syntax_light = bool(light)
        self.viewport().update()

    def focusNextPrevChild(self, _next: bool) -> bool:
        """Tab/Shift+Tab stay in the editor (indent / unindent)."""
        return False

    def event(self, event: QEvent | None) -> bool:
        if (
            event is not None
            and event.type() == QEvent.Type.KeyPress
            and intercept_tab_event(self, event)
        ):
            return True
        return super().event(event)

    def set_spell_engine(self, engine: SpellEngine | None) -> None:
        """Attach viewport spell checker (None disables)."""
        self._spell = engine
        self._schedule_spell_refresh()

    def _on_buffer_changed(self) -> None:
        self._token_cache.invalidate()
        self._schedule_spell_refresh()

    def _schedule_spell_refresh(self, *_args: object) -> None:
        self._spell_debounce.start()

    def _refresh_spell_spans(self) -> None:
        refresh_visible_spans(self)

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
        return editor_column_rect(self)

    def _multi_edit_spans(self) -> list[tuple[int, int, int]]:
        return editor_multi_spans(self)

    def _update_brace_match(self) -> None:
        update_brace_match(self)

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
        return clip_has(self)

    def replace_word_on_line(self, line: int, start_col: int, end_col: int, new_text: str) -> None:
        clip_replace_word(self, line, start_col, end_col, new_text)

    def selected_text(self) -> str:
        return clip_selected(self)

    def copy(self) -> None:
        clip_copy(self)

    def cut(self) -> None:
        clip_cut(self)

    def paste(self) -> None:
        clip_paste(self)

    def select_all(self) -> None:
        clip_select_all(self)

    def _clear_selection(self) -> None:
        clip_clear(self)

    def _normalized_selection(self) -> tuple[int, int, int, int]:
        return clip_norm(self)

    def _selection_cols_on_line(self, line: int) -> tuple[int, int] | None:
        return clip_cols(self, line)

    def _delete_selection(self, *, emit: bool = True) -> bool:
        return clip_delete(self, emit=emit)

    def _begin_selection_if_needed(self, shift: bool) -> None:
        clip_begin_sel(self, shift)

    def toPlainText(self) -> str:
        return export_editor_text(self)

    def viewport_text(self) -> str:
        """Visible lines only (J2.3). Does not materialize the full buffer."""
        first = max(0, int(self.verticalScrollBar().value()))
        lh = max(1, int(getattr(self, "_line_height", 18) or 18))
        vis = max(1, int(self.viewport().height() or 0) // lh)
        total = self._line_count()
        if total <= 0:
            return ""
        last = min(total, first + vis)
        if last <= first:
            return self._doc.line_text(min(first, total - 1))
        return "\n".join(self._doc.line_text(i) for i in range(first, last))

    def set_line_numbers_visible(self, visible: bool) -> None:
        self._show_line_numbers = visible
        self._gutter_width = 56 if visible else 0
        self.viewport().update()

    def set_word_wrap(self, enabled: bool) -> None:
        self._word_wrap = enabled

    def set_font_point_size(self, size: int) -> None:
        chrome_set_font(self, size)

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
        apply_brace_enabled(self, enabled)

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
        chrome_toggle_bookmark(self)

    def get_bookmarks(self) -> list[int]:
        return sorted(self._bookmarks)

    def set_bookmarks(self, lines: list[int] | set[int]) -> None:
        self._bookmarks = {int(x) for x in lines if int(x) >= 0}
        self.viewport().update()

    def next_bookmark(self) -> bool:
        return chrome_next_bookmark(self)

    def prev_bookmark(self) -> bool:
        return chrome_prev_bookmark(self)

    def has_bookmark(self, line: int) -> bool:
        return line in self._bookmarks

    def apply_theme_palette(self, theme_id: str) -> None:
        chrome_apply_theme(self, theme_id)

    def zoom_in_one(self) -> None:
        chrome_zoom_in(self)

    def zoom_out_one(self) -> None:
        chrome_zoom_out(self)

    def reset_zoom(self) -> None:
        chrome_zoom_reset(self)

    def find_text(
        self,
        needle: str,
        *,
        case_sensitive: bool = False,
        backward: bool = False,
        wrap: bool = True,
        use_regex: bool = False,
    ) -> bool:
        return find_in_editor(
            self,
            needle,
            case_sensitive=case_sensitive,
            backward=backward,
            wrap=wrap,
            use_regex=use_regex,
        )

    def replace_text(
        self,
        needle: str,
        replacement: str,
        *,
        case_sensitive: bool = False,
        use_regex: bool = False,
    ) -> bool:
        return replace_in_editor(
            self,
            needle,
            replacement,
            case_sensitive=case_sensitive,
            use_regex=use_regex,
        )

    def replace_all_text(
        self,
        needle: str,
        replacement: str,
        *,
        case_sensitive: bool = False,
        use_regex: bool = False,
        max_replacements: int = MAX_REPLACE_ALL,
    ) -> int:
        return replace_all_in_editor(
            self,
            needle,
            replacement,
            case_sensitive=case_sensitive,
            use_regex=use_regex,
            max_replacements=max_replacements,
        )

    def undo(self) -> None:
        undo_editor(self)

    def redo(self) -> None:
        redo_editor(self)

    def centerCursor(self) -> None:
        self._ensure_visible(self._cursor_line)

    # --- metrics / scroll ---------------------------------------------

    def _recalc_metrics(self) -> None:
        metrics_recalc(self)

    def _line_count(self) -> int:
        return metrics_line_count(self)

    def _update_scrollbars(self) -> None:
        metrics_scrollbars(self)

    def _wrap_display_rows(self, text: str) -> list[tuple[int, int, str]]:
        return metrics_wrap(self, text)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_scrollbars()

    def scrollContentsBy(self, dx: int, dy: int) -> None:
        self.viewport().scroll(dx, dy)
        self.viewport().update()

    def _ensure_visible(self, line: int) -> None:
        metrics_ensure_visible(self, line)

    # --- paint --------------------------------------------------------

    def paintEvent(self, event: QPaintEvent | None) -> None:
        paint_viewport(self, event)

    def wheelEvent(self, event: QWheelEvent | None) -> None:
        if not handle_wheel(self, event):
            super().wheelEvent(event)

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        if not handle_key_press(self, event):
            super().keyPressEvent(event)

    def mousePressEvent(self, event) -> None:
        if not handle_mouse_press(self, event):
            super().mousePressEvent(event)

    def contextMenuEvent(self, event: QContextMenuEvent | None) -> None:
        handle_context_menu(self, event)

    def viewportEvent(self, event: QEvent | None) -> bool:
        handled = handle_viewport_event(self, event)
        if handled is None:
            return super().viewportEvent(event)
        if event is not None and event.type() != QEvent.Type.ContextMenu:
            return bool(handled) or super().viewportEvent(event)
        return True

    def mouseMoveEvent(self, event) -> None:
        if not handle_mouse_move(self, event):
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        handle_mouse_release(self, event)
        super().mouseReleaseEvent(event)

    def _hit_test(self, pos: QPoint) -> tuple[int, int]:
        return hit_test(self, pos)

    # --- edits (piece table + incremental line index + undo) ----------

    def _byte_offset_at_cursor(self) -> int:
        return edit_byte_offset(self)

    def _col_to_byte(self, line: int, col: int) -> int:
        return editor_col_to_byte(self, line, col)

    def _byte_to_col(self, line: int, byte_off: int) -> int:
        return editor_byte_to_col(self, line, byte_off)

    def _replace_char_span(
        self,
        line: int,
        start_col: int,
        end_col: int,
        replacement: str,
        *,
        emit: bool = True,
    ) -> None:
        replace_char_span(self, line, start_col, end_col, replacement, emit=emit)

    def _insert_bytes_tracked(self, offset: int, data: bytes) -> None:
        track_insert(self, offset, data)

    def _delete_bytes_tracked(self, offset: int, length: int) -> None:
        track_delete(self, offset, length)

    def _place_cursor_at(self, byte_off: int) -> None:
        place_cursor_at(self, byte_off)

    def _emit_edit(self, *, clear_redo: bool = True) -> None:
        emit_edit(self)

    def insert(self, text: str) -> None:
        """EditorSurface: insert text at the caret."""
        insert_at_cursor(self, text)

    def _insert_at_cursor(self, text: str) -> None:
        insert_at_cursor(self, text)

    def _backspace(self) -> None:
        cursors_backspace(self)

    def _delete_forward(self) -> None:
        cursors_delete_forward(self)

    def cursor_line_col(self) -> tuple[int, int]:
        return self._cursor_line + 1, self._cursor_col + 1

    def _try_snippet_or_complete(self) -> bool:
        return try_snippet_or_complete(self)

    def _newline_with_indent(self) -> str:
        return newline_for_editor(self)

    def indent_line(self) -> None:
        keys_indent_line(self)

    def unindent_line(self) -> None:
        keys_unindent_line(self)

    def duplicate_line(self) -> None:
        from magiceditor.ui.virtual_cursors import duplicate_current_line

        duplicate_current_line(self)
