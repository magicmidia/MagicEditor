"""Single document tab: classic or virtual editor + optional preview."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import QSplitter, QVBoxLayout, QWidget

from magiceditor.core.piece_table import PieceTable
from magiceditor.core.syntax.detect import detect_language
from magiceditor.preview.web_preview import WebPreview
from magiceditor.services.document import Document
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
        self._huge = document.huge_mode
        self._highlighter: MagicHighlighter | None = None

        if self._huge:
            virtual = VirtualEditor(document, self)
            virtual.set_language(self._language)
            self.editor: TextEditor | VirtualEditor = virtual
            self.editor.cursorPositionChanged.connect(self._on_virtual_cursor)
            self.editor.textChanged.connect(self._on_virtual_text)
            self.editor.modificationChanged.connect(self._on_virtual_mod)
        else:
            classic = TextEditor(self)
            self.editor = classic
            self._highlighter = MagicHighlighter(classic.document(), self._language)
            classic.setPlainText(document.text())
            classic.document().setModified(False)
            classic.textChanged.connect(self._on_text_changed)
            classic.cursorPositionChanged.connect(self._on_cursor)

        self.preview = WebPreview(self)
        self.preview.hide()

        self._splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self._splitter.addWidget(self.editor)
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
        assert isinstance(self.editor, TextEditor)
        name = self.document.title.lower()
        text = self.editor.toPlainText()
        if name.endswith((".html", ".htm")) or self._language == "html":
            self.preview.set_html(text)
        else:
            self.preview.set_markdown(text)

    def sync_document_from_editor(self) -> None:
        if self._huge:
            # Virtual editor already mutates the piece table in place.
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

