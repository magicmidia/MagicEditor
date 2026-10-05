"""Single document tab: VirtualEditor viewport + optional preview."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QSplitter, QVBoxLayout, QWidget

from magiceditor.core.syntax.detect import detect_language
from magiceditor.services.document import Document
from magiceditor.ui.minimap_widget import MinimapWidget
from magiceditor.ui.syntax_highlighter import MagicHighlighter
from magiceditor.ui.virtual_editor import VirtualEditor


class EditorTab(QWidget):
    """Hosts one document with optional live preview."""

    modification_changed = pyqtSignal()
    cursor_info_changed = pyqtSignal(int, int)  # line, column (1-based)
    language_changed = pyqtSignal(str)

    def __init__(self, document: Document, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.document = document
        self._preview_visible = False
        self._language = detect_language(document.path, document.title)
        # Viewport path for all docs so spell/multi-cursor/power features always work.
        # huge_mode still gates mmap / full-load policy in document I/O.
        self._huge = document.huge_mode
        self._highlighter: MagicHighlighter | None = None
        # Spell dictionary languages for this document (union). Empty = use session default.
        self.spell_languages: list[str] = []
        self.spell_force: bool | None = None  # None = auto by syntax language

        virtual = VirtualEditor(document, self)
        virtual.set_language(self._language)
        self.editor: VirtualEditor = virtual
        self.editor.cursorPositionChanged.connect(self._on_virtual_cursor)
        self.editor.textChanged.connect(self._on_virtual_text)
        self.editor.modificationChanged.connect(self._on_virtual_mod)

        self.preview = None
        self._preview_slot = QWidget(self)
        self._preview_slot.hide()

        self.minimap = MinimapWidget(self)
        self.minimap.hide()
        self.minimap.jump_ratio.connect(self._on_minimap_jump)
        self._minimap_timer = QTimer(self)
        self._minimap_timer.setSingleShot(True)
        self._minimap_timer.setInterval(120)
        self._minimap_timer.timeout.connect(self._refresh_minimap)
        self.editor.textChanged.connect(self._schedule_minimap)
        self.editor.cursorPositionChanged.connect(self._refresh_minimap_viewport)
        self.editor.verticalScrollBar().valueChanged.connect(self._refresh_minimap_viewport)

        editor_row = QWidget(self)
        row_lay = QHBoxLayout(editor_row)
        row_lay.setContentsMargins(0, 0, 0, 0)
        row_lay.setSpacing(0)
        row_lay.addWidget(self.editor, 1)
        row_lay.addWidget(self.minimap, 0)

        self._splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self._splitter.addWidget(editor_row)
        self._splitter.addWidget(self._preview_slot)
        self._splitter.setStretchFactor(0, 3)
        self._splitter.setStretchFactor(1, 2)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._splitter, 1)

    @property
    def is_huge(self) -> bool:
        return self._huge

    @property
    def language(self) -> str:
        return self._language

    def set_language(self, language: str) -> None:
        self._language = language
        if self._highlighter is not None:
            self._highlighter.set_language(language)
        self.editor.set_language(language)
        self.language_changed.emit(language)

    def refresh_language_from_path(self) -> str:
        """Re-detect syntax from the document path/title (e.g. after Save As)."""
        lang = detect_language(self.document.path, self.document.title)
        if lang != self._language:
            self.set_language(lang)
        else:
            self.editor.viewport().update()
        return self._language

    def set_minimap_visible(self, visible: bool) -> None:
        """Show/hide minimap; huge documents keep it off (C3/K13 cost guard)."""
        if visible and self._huge:
            self.minimap.set_enabled(False)
            return
        self.minimap.set_enabled(bool(visible))
        if visible:
            self._refresh_minimap()
            self._refresh_minimap_viewport()

    def minimap_visible(self) -> bool:
        return self.minimap.isVisible()

    def set_word_completion(self, enabled: bool) -> None:
        self.editor.set_word_completion(enabled)

    def _schedule_minimap(self) -> None:
        if self._huge or not self.minimap.isVisible():
            return
        self._minimap_timer.start()

    def _refresh_minimap(self) -> None:
        if self._huge or not self.minimap.isVisible():
            return
        lines: list[str] = []
        total = self.document.line_index().line_count
        # Cap sample for huge files
        step = max(1, total // 4000) if total > 4000 else 1
        for i in range(0, total, step):
            try:
                lines.append(self.document.line_text(i))
            except IndexError:
                break
            if len(lines) >= 4000:
                break
        self.minimap.set_document_lines(lines)

    def _refresh_minimap_viewport(self) -> None:
        if not self.minimap.isVisible():
            return
        total = max(1, self.document.line_index().line_count)
        first = self.editor.verticalScrollBar().value()
        lh = getattr(self.editor, "_line_height", 18)
        vis = max(1, self.editor.viewport().height() // max(1, int(lh)))
        self.minimap.set_viewport_ratio(first / total, min(1.0, (first + vis) / total))

    def _on_minimap_jump(self, ratio: float) -> None:
        total = max(1, self.document.line_index().line_count)
        line = int(ratio * (total - 1))
        self.editor.goto_line(line, 0)

    def goto_line(self, line: int, column: int = 0) -> None:
        """Move caret to 1-based line/column."""
        line0 = max(0, line - 1)
        col0 = max(0, column - 1)
        self.editor.goto_line(line0, col0)

    def set_syntax_light_theme(self, light: bool) -> None:
        if self._highlighter is not None:
            self._highlighter.set_light_theme(light)
        self.editor.set_syntax_light_theme(light)

    def _on_virtual_cursor(self) -> None:
        assert isinstance(self.editor, VirtualEditor)
        line, col = self.editor.cursor_line_col()
        self.cursor_info_changed.emit(line, col)

    def _on_virtual_text(self) -> None:
        self.modification_changed.emit()

    def _on_virtual_mod(self, _mod: bool) -> None:
        self.modification_changed.emit()

    def _ensure_preview(self):
        """Create WebPreview only when the user opens Preview (K7)."""
        if self.preview is None:
            from magiceditor.preview.web_preview import WebPreview

            self.preview = WebPreview(self)
            self._splitter.replaceWidget(1, self.preview)
            self.preview.hide()
        return self.preview

    def toggle_preview(self) -> bool:
        if self._huge:
            # Preview of multi-GB files is not practical.
            return False
        self._preview_visible = not self._preview_visible
        preview = self._ensure_preview()
        preview.setVisible(self._preview_visible)
        if self._preview_visible:
            self.refresh_preview()
        return self._preview_visible

    def apply_preview_theme(self, theme_id: str) -> None:
        if self.preview is None:
            return
        self.preview.apply_theme(theme_id)
        if self._preview_visible:
            self.refresh_preview()

    def refresh_preview(self) -> None:
        if self._huge:
            return
        preview = self._ensure_preview()
        theme_id = self._preview_theme_id()
        preview.apply_theme(theme_id)
        name = self.document.title.lower()
        text = self.export_text()
        if name.endswith((".html", ".htm")) or self._language == "html":
            preview.set_html(text)
        else:
            preview.set_markdown(text)

    def _preview_theme_id(self) -> str:
        win = self.window()
        themes = getattr(win, "_themes", None)
        current = getattr(themes, "current", None)
        return str(current) if current else "luminous_void"

    def sync_document_from_editor(self) -> None:
        # Virtual editor mutates the piece table in place.
        return

    def viewport_text(self) -> str:
        return self.editor.viewport_text()

    def export_text(self) -> str:
        return self.document.full_text()

    def set_word_wrap(self, enabled: bool) -> None:
        self.editor.set_word_wrap(enabled)

    def set_line_numbers(self, visible: bool) -> None:
        self.editor.set_line_numbers_visible(visible)

    def zoom_in(self) -> None:
        self.editor.zoom_in_one()

    def zoom_out(self) -> None:
        self.editor.zoom_out_one()

    def zoom_reset(self) -> None:
        self.editor.reset_zoom()

    def undo(self) -> None:
        self.editor.undo()

    def redo(self) -> None:
        self.editor.redo()

    def cut(self) -> None:
        self.editor.cut()

    def copy(self) -> None:
        self.editor.copy()

    def paste(self) -> None:
        self.editor.paste()

    def select_all(self) -> None:
        self.editor.select_all()

    def indent(self) -> None:
        self.editor.indent_line()

    def unindent(self) -> None:
        self.editor.unindent_line()

    def duplicate_line(self) -> None:
        self.editor.duplicate_line()

    def line_count(self) -> int:
        return self.document.line_index().line_count

    def current_line(self) -> int:
        """1-based current line."""
        line, _ = self.editor.cursor_line_col()
        return line

    def toggle_bookmark(self) -> None:
        self.editor.toggle_bookmark()

    def get_bookmarks(self) -> list[int]:
        return self.editor.get_bookmarks()

    def set_bookmarks(self, lines: list[int] | set[int]) -> None:
        self.editor.set_bookmarks(lines)

    def next_bookmark(self) -> bool:
        return self.editor.next_bookmark()

    def prev_bookmark(self) -> bool:
        return self.editor.prev_bookmark()

    def cursor_line_col_1based(self) -> tuple[int, int]:
        return self.current_line(), self.editor.cursor_line_col()[1]
