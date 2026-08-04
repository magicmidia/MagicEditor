"""Single document tab: classic or virtual editor + optional preview."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import QHBoxLayout, QSplitter, QVBoxLayout, QWidget

from magiceditor.core.piece_table import PieceTable
from magiceditor.core.syntax.detect import detect_language
from magiceditor.preview.web_preview import WebPreview
from magiceditor.services.document import Document
from magiceditor.ui.minimap_widget import MinimapWidget
from magiceditor.ui.syntax_highlighter import MagicHighlighter
from magiceditor.ui.text_editor import TextEditor
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
        self.editor: TextEditor | VirtualEditor = virtual
        self.editor.cursorPositionChanged.connect(self._on_virtual_cursor)
        self.editor.textChanged.connect(self._on_virtual_text)
        self.editor.modificationChanged.connect(self._on_virtual_mod)

        self.preview = WebPreview(self)
        self.preview.hide()

        self.minimap = MinimapWidget(self)
        self.minimap.hide()
        self.minimap.jump_ratio.connect(self._on_minimap_jump)
        if isinstance(self.editor, VirtualEditor):
            self.editor.textChanged.connect(self._refresh_minimap)
            self.editor.cursorPositionChanged.connect(self._refresh_minimap_viewport)
            self.editor.verticalScrollBar().valueChanged.connect(
                self._refresh_minimap_viewport
            )

        editor_row = QWidget(self)
        row_lay = QHBoxLayout(editor_row)
        row_lay.setContentsMargins(0, 0, 0, 0)
        row_lay.setSpacing(0)
        row_lay.addWidget(self.editor, 1)
        row_lay.addWidget(self.minimap, 0)

        self._splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self._splitter.addWidget(editor_row)
        self._splitter.addWidget(self.preview)
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
        if isinstance(self.editor, VirtualEditor):
            self.editor.set_language(language)
        self.language_changed.emit(language)

    def set_minimap_visible(self, visible: bool) -> None:
        """Show/hide minimap; degrades (hides) for huge documents."""
        if self._huge and visible:
            # Still allow density sample but cap cost
            pass
        self.minimap.set_enabled(bool(visible))
        if visible:
            self._refresh_minimap()
            self._refresh_minimap_viewport()

    def minimap_visible(self) -> bool:
        return self.minimap.isVisible()

    def set_word_completion(self, enabled: bool) -> None:
        if isinstance(self.editor, VirtualEditor):
            self.editor.set_word_completion(enabled)

    def _refresh_minimap(self) -> None:
        if not self.minimap.isVisible():
            return
        lines: list[str] = []
        if isinstance(self.editor, VirtualEditor):
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
        else:
            lines = self.editor.toPlainText().splitlines()[:4000]
        self.minimap.set_document_lines(lines)

    def _refresh_minimap_viewport(self) -> None:
        if not self.minimap.isVisible():
            return
        if isinstance(self.editor, VirtualEditor):
            total = max(1, self.document.line_index().line_count)
            first = self.editor.verticalScrollBar().value()
            lh = getattr(self.editor, "_line_height", 18)
            vis = max(1, self.editor.viewport().height() // max(1, int(lh)))
            self.minimap.set_viewport_ratio(first / total, min(1.0, (first + vis) / total))
        else:
            sb = self.editor.verticalScrollBar()
            mx = max(1, sb.maximum())
            self.minimap.set_viewport_ratio(sb.value() / mx, min(1.0, (sb.value() + 10) / mx))

    def _on_minimap_jump(self, ratio: float) -> None:
        if isinstance(self.editor, VirtualEditor):
            total = max(1, self.document.line_index().line_count)
            line = int(ratio * (total - 1))
            self.editor.goto_line(line, 0)
        else:
            sb = self.editor.verticalScrollBar()
            sb.setValue(int(ratio * sb.maximum()))

    def goto_line(self, line: int, column: int = 0) -> None:
        """Move caret to 1-based line/column."""
        line0 = max(0, line - 1)
        col0 = max(0, column - 1)
        if isinstance(self.editor, VirtualEditor):
            self.editor.goto_line(line0, col0)
            return
        assert isinstance(self.editor, TextEditor)
        block = self.editor.document().findBlockByNumber(line0)
        if not block.isValid():
            return
        cursor = QTextCursor(block)
        cursor.movePosition(
            QTextCursor.MoveOperation.Right,
            QTextCursor.MoveMode.MoveAnchor,
            min(col0, block.length() - 1),
        )
        self.editor.setTextCursor(cursor)
        self.editor.centerCursor()
        self.editor.setFocus()

    def set_syntax_light_theme(self, light: bool) -> None:
        if self._highlighter is not None:
            self._highlighter.set_light_theme(light)

    def _on_text_changed(self) -> None:
        assert isinstance(self.editor, TextEditor)
        text = self.editor.toPlainText()
        self.document.buffer = PieceTable(text)
        self.document.mark_modified()
        self.modification_changed.emit()
        if self._preview_visible:
            self.refresh_preview()

    def _on_cursor(self) -> None:
        assert isinstance(self.editor, TextEditor)
        cursor = self.editor.textCursor()
        self.cursor_info_changed.emit(cursor.blockNumber() + 1, cursor.positionInBlock() + 1)

    def _on_virtual_cursor(self) -> None:
        assert isinstance(self.editor, VirtualEditor)
        line, col = self.editor.cursor_line_col()
        self.cursor_info_changed.emit(line, col)

    def _on_virtual_text(self) -> None:
        self.modification_changed.emit()

    def _on_virtual_mod(self, _mod: bool) -> None:
        self.modification_changed.emit()

    def toggle_preview(self) -> bool:
        if self._huge:
            # Preview of multi-GB files is not practical.
            return False
        self._preview_visible = not self._preview_visible
        self.preview.setVisible(self._preview_visible)
        if self._preview_visible:
            self.refresh_preview()
        return self._preview_visible

    def refresh_preview(self) -> None:
        if self._huge:
            return
        name = self.document.title.lower()
        text = self.export_text()
        if name.endswith((".html", ".htm")) or self._language == "html":
            self.preview.set_html(text)
        else:
            self.preview.set_markdown(text)

    def sync_document_from_editor(self) -> None:
        # Virtual editor mutates the piece table in place.
        if isinstance(self.editor, VirtualEditor):
            return
        assert isinstance(self.editor, TextEditor)
        self.document.buffer = PieceTable(self.editor.toPlainText())

    def export_text(self) -> str:
        if isinstance(self.editor, VirtualEditor):
            return self.editor.toPlainText()
        return self.editor.toPlainText()

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
        if isinstance(self.editor, VirtualEditor):
            self.editor.select_all()
        else:
            assert isinstance(self.editor, TextEditor)
            self.editor.selectAll()

    def indent(self) -> None:
        if isinstance(self.editor, VirtualEditor):
            self.editor.indent_line()
        else:
            assert isinstance(self.editor, TextEditor)
            cur = self.editor.textCursor()
            cur.insertText("    ")

    def unindent(self) -> None:
        if isinstance(self.editor, VirtualEditor):
            self.editor.unindent_line()
        else:
            assert isinstance(self.editor, TextEditor)
            cur = self.editor.textCursor()
            cur.movePosition(cur.MoveOperation.StartOfBlock)
            block = cur.block().text()
            strip = 0
            if block.startswith("\t"):
                strip = 1
            elif block.startswith("    "):
                strip = 4
            elif block.startswith(" "):
                strip = min(4, len(block) - len(block.lstrip(" ")))
            if strip:
                cur.movePosition(
                    cur.MoveOperation.Right,
                    cur.MoveMode.KeepAnchor,
                    strip,
                )
                cur.removeSelectedText()

    def duplicate_line(self) -> None:
        if isinstance(self.editor, VirtualEditor):
            self.editor.duplicate_line()
        else:
            assert isinstance(self.editor, TextEditor)
            cur = self.editor.textCursor()
            cur.select(cur.SelectionType.BlockUnderCursor)
            text = cur.selectedText()
            # Qt uses U+2029 as block separator in selectedText
            text = text.replace("\u2029", "\n")
            cur.movePosition(cur.MoveOperation.EndOfBlock)
            cur.insertText("\n" + text)

    def line_count(self) -> int:
        if isinstance(self.editor, VirtualEditor):
            return self.document.line_index().line_count
        assert isinstance(self.editor, TextEditor)
        return max(1, self.editor.blockCount())

    def current_line(self) -> int:
        """1-based current line."""
        if isinstance(self.editor, VirtualEditor):
            line, _ = self.editor.cursor_line_col()
            return line
        assert isinstance(self.editor, TextEditor)
        return self.editor.textCursor().blockNumber() + 1

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
        return self.current_line(), (
            self.editor.cursor_line_col()[1]
            if isinstance(self.editor, VirtualEditor)
            else self.editor.textCursor().positionInBlock() + 1
        )

