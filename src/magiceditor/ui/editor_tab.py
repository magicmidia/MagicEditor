"""Single document tab: editor + optional preview split."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QSplitter, QVBoxLayout, QWidget

from magiceditor.core.piece_table import PieceTable
from magiceditor.preview.web_preview import WebPreview
from magiceditor.services.document import Document
from magiceditor.ui.text_editor import TextEditor


class EditorTab(QWidget):
    """Hosts one document with optional live preview."""

    modification_changed = pyqtSignal()
    cursor_info_changed = pyqtSignal(int, int)  # line, column (1-based)

    def __init__(self, document: Document, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.document = document
        self._preview_visible = False

        self.editor = TextEditor(self)
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

        self.editor.setPlainText(document.text())
        self.editor.document().setModified(False)
        self.editor.textChanged.connect(self._on_text_changed)
        self.editor.cursorPositionChanged.connect(self._on_cursor)

    def _on_text_changed(self) -> None:
        text = self.editor.toPlainText()
        self.document.buffer = PieceTable(text)
        self.document.mark_modified()
        self.modification_changed.emit()
        if self._preview_visible:
            self.refresh_preview()

    def _on_cursor(self) -> None:
        cursor = self.editor.textCursor()
        self.cursor_info_changed.emit(cursor.blockNumber() + 1, cursor.positionInBlock() + 1)

    def toggle_preview(self) -> bool:
        self._preview_visible = not self._preview_visible
        self.preview.setVisible(self._preview_visible)
        if self._preview_visible:
            self.refresh_preview()
        return self._preview_visible

    def refresh_preview(self) -> None:
        name = self.document.title.lower()
        text = self.editor.toPlainText()
        if name.endswith((".html", ".htm")):
            self.preview.set_html(text)
        else:
            self.preview.set_markdown(text)

    def sync_document_from_editor(self) -> None:
        self.document.buffer = PieceTable(self.editor.toPlainText())

    def set_word_wrap(self, enabled: bool) -> None:
        self.editor.set_word_wrap(enabled)

    def set_line_numbers(self, visible: bool) -> None:
        self.editor.set_line_numbers_visible(visible)
