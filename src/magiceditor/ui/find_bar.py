"""Inline find/replace bar (Ctrl+F / Ctrl+H)."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QKeySequence, QTextCursor, QTextDocument
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from magiceditor.ui.text_editor import TextEditor


class FindBar(QWidget):
    """Compact find/replace strip docked above the editor."""

    closed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._editor: TextEditor | None = None
        self.setObjectName("findBar")

        self.find_input = QLineEdit(self)
        self.find_input.setPlaceholderText("Find…")
        self.find_input.returnPressed.connect(self.find_next)
        self.replace_input = QLineEdit(self)
        self.replace_input.setPlaceholderText("Replace…")

        self.case_box = QCheckBox("Match case")
        self.regex_box = QCheckBox("Regex")

        self._count = QLabel("")
        self._count.setObjectName("findCount")

        btn_next = QPushButton("Next")
        btn_prev = QPushButton("Prev")
        btn_replace = QPushButton("Replace")
        btn_all = QPushButton("Replace all")
        btn_close = QToolButton(self)
        btn_close.setText("✕")
        btn_close.setShortcut(QKeySequence("Esc"))
        btn_close.clicked.connect(self._close)

        btn_next.clicked.connect(self.find_next)
        btn_prev.clicked.connect(self.find_prev)
        btn_replace.clicked.connect(self.replace_one)
        btn_all.clicked.connect(self.replace_all)

        row1 = QHBoxLayout()
        row1.setContentsMargins(12, 10, 12, 6)
        row1.setSpacing(8)
        row1.addWidget(self.find_input, 1)
        row1.addWidget(btn_prev)
        row1.addWidget(btn_next)
        row1.addWidget(self.case_box)
        row1.addWidget(self.regex_box)
        row1.addWidget(self._count)
        row1.addWidget(btn_close)

        row2 = QHBoxLayout()
        row2.setContentsMargins(12, 0, 12, 10)
        row2.setSpacing(8)
        row2.addWidget(self.replace_input, 1)
        row2.addWidget(btn_replace)
        row2.addWidget(btn_all)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(row1)
        layout.addLayout(row2)

    def attach(self, editor: TextEditor) -> None:
        self._editor = editor

    def open_find(self, *, replace: bool = False) -> None:
        self.setVisible(True)
        self.replace_input.setVisible(replace)
        # keep replace buttons usable only when replace mode
        self.find_input.setFocus()
        self.find_input.selectAll()
        if self._editor is not None:
            cursor = self._editor.textCursor()
            if cursor.hasSelection():
                self.find_input.setText(cursor.selectedText().replace("\u2029", "\n"))

    def _flags(self) -> QTextDocument.FindFlag:
        flags = QTextDocument.FindFlag(0)
        if self.case_box.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        return flags

    def find_next(self) -> None:
        self._find(backward=False)

    def find_prev(self) -> None:
        self._find(backward=True)

    def _find(self, *, backward: bool) -> None:
        if self._editor is None:
            return
        text = self.find_input.text()
        if not text:
            return
        flags = self._flags()
        if backward:
            flags |= QTextDocument.FindFlag.FindBackward
        found = self._editor.find(text, flags)
        if not found:
            # wrap
            cursor = self._editor.textCursor()
            cursor.movePosition(
                QTextCursor.MoveOperation.End if backward else QTextCursor.MoveOperation.Start
            )
            self._editor.setTextCursor(cursor)
            self._editor.find(text, flags)
        self._update_count()

    def replace_one(self) -> None:
        if self._editor is None:
            return
        cursor = self._editor.textCursor()
        if cursor.hasSelection() and cursor.selectedText() == self.find_input.text():
            cursor.insertText(self.replace_input.text())
        self.find_next()

    def replace_all(self) -> None:
        if self._editor is None:
            return
        needle = self.find_input.text()
        if not needle:
            return
        repl = self.replace_input.text()
        doc = self._editor.document()
        cursor = QTextCursor(doc)
        cursor.beginEditBlock()
        count = 0
        flags = self._flags()
        while True:
            cursor = doc.find(needle, cursor, flags)
            if cursor.isNull():
                break
            cursor.insertText(repl)
            count += 1
        cursor.endEditBlock()
        self._count.setText(f"{count} replaced")

    def _update_count(self) -> None:
        if self._editor is None:
            return
        needle = self.find_input.text()
        if not needle:
            self._count.setText("")
            return
        # lightweight count for small/medium docs
        text = self._editor.toPlainText()
        if not self.case_box.isChecked():
            n = text.lower().count(needle.lower())
        else:
            n = text.count(needle)
        self._count.setText(f"{n} matches")

    def _close(self) -> None:
        self.hide()
        self.closed.emit()
        if self._editor is not None:
            self._editor.setFocus()
