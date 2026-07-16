"""Modal Find / Find & Replace dialogs."""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut, QTextCursor, QTextDocument
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class FindDialog(QDialog):
    """Centered modal for search (and optional replace).

    Works with ``TextEditor`` (QPlainTextEdit) and ``VirtualEditor``
    (duck-typed ``find_text`` / ``replace_text``).
    """

    def __init__(
        self,
        editor: Any,
        parent: QWidget | None = None,
        *,
        replace_mode: bool = False,
    ) -> None:
        super().__init__(parent)
        self._editor = editor
        self._replace_mode = replace_mode
        self._virtual = hasattr(editor, "find_text")
        self.setModal(True)
        self.setWindowTitle("Find and Replace" if replace_mode else "Find")
        self.setMinimumWidth(420)
        self.setObjectName("findDialog")

        self.find_input = QLineEdit(self)
        self.find_input.setPlaceholderText("Find…")
        self.replace_input = QLineEdit(self)
        self.replace_input.setPlaceholderText("Replace with…")
        self.replace_input.setVisible(replace_mode)

        self.case_box = QCheckBox("Match case", self)
        self.wrap_box = QCheckBox("Wrap around", self)
        self.wrap_box.setChecked(True)

        self._status = QLabel("", self)
        self._status.setObjectName("findDialogStatus")
        if self._virtual and replace_mode:
            self._status.setText("Replace works in huge-file mode (capped replace-all).")

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.addRow("Find:", self.find_input)
        if replace_mode:
            form.addRow("Replace:", self.replace_input)

        options = QHBoxLayout()
        options.setSpacing(16)
        options.addWidget(self.case_box)
        options.addWidget(self.wrap_box)
        options.addStretch(1)

        btn_prev = QPushButton("Find Previous", self)
        btn_next = QPushButton("Find Next", self)
        btn_next.setDefault(True)
        btn_replace = QPushButton("Replace", self)
        btn_all = QPushButton("Replace All", self)
        btn_close = QPushButton("Close", self)

        btn_prev.clicked.connect(self.find_prev)
        btn_next.clicked.connect(self.find_next)
        btn_replace.clicked.connect(self.replace_one)
        btn_all.clicked.connect(self.replace_all)
        btn_close.clicked.connect(self.reject)

        btn_replace.setVisible(replace_mode)
        btn_all.setVisible(replace_mode)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        buttons.addWidget(btn_prev)
        buttons.addWidget(btn_next)
        if replace_mode:
            buttons.addWidget(btn_replace)
            buttons.addWidget(btn_all)
        buttons.addStretch(1)
        buttons.addWidget(btn_close)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)
        root.addLayout(form)
        root.addLayout(options)
        root.addWidget(self._status)
        root.addLayout(buttons)

        self.find_input.returnPressed.connect(self.find_next)
        QShortcut(QKeySequence("Esc"), self, activated=self.reject)

        if not self._virtual:
            cursor = editor.textCursor()
            if cursor.hasSelection():
                sel = cursor.selectedText().replace("\u2029", "\n")
                if "\n" not in sel:
                    self.find_input.setText(sel)
        self.find_input.selectAll()
        self.find_input.setFocus()

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
        text = self.find_input.text()
        if not text:
            self._status.setText("Enter text to find.")
            return

        if self._virtual:
            found = self._editor.find_text(
                text,
                case_sensitive=self.case_box.isChecked(),
                backward=backward,
                wrap=self.wrap_box.isChecked(),
            )
            if found:
                self._status.setText("Match found.")
                self._editor.centerCursor()
            else:
                self._status.setText("No matches.")
            return

        flags = self._flags()
        if backward:
            flags |= QTextDocument.FindFlag.FindBackward
        found = self._editor.find(text, flags)
        if not found and self.wrap_box.isChecked():
            cursor = self._editor.textCursor()
            cursor.movePosition(
                QTextCursor.MoveOperation.End if backward else QTextCursor.MoveOperation.Start
            )
            self._editor.setTextCursor(cursor)
            found = self._editor.find(text, flags)
        if found:
            self._status.setText("Match found.")
            self._editor.centerCursor()
        else:
            self._status.setText("No matches.")

    def replace_one(self) -> None:
        if not self._replace_mode:
            return
        needle = self.find_input.text()
        if not needle:
            self._status.setText("Enter text to find.")
            return
        repl = self.replace_input.text()

        if self._virtual and hasattr(self._editor, "replace_text"):
            ok = self._editor.replace_text(
                needle,
                repl,
                case_sensitive=self.case_box.isChecked(),
            )
            self._status.setText("Replaced 1 match." if ok else "No matches.")
            return

        cursor = self._editor.textCursor()
        if cursor.hasSelection() and self._selection_matches(cursor, needle):
            cursor.insertText(repl)
            self._status.setText("Replaced 1 match.")
        self.find_next()

    def replace_all(self) -> None:
        if not self._replace_mode:
            return
        needle = self.find_input.text()
        if not needle:
            self._status.setText("Enter text to find.")
            return
        repl = self.replace_input.text()

        if self._virtual and hasattr(self._editor, "replace_all_text"):
            count = self._editor.replace_all_text(
                needle,
                repl,
                case_sensitive=self.case_box.isChecked(),
            )
            extra = " (capped)" if count >= 50_000 else ""
            self._status.setText(f"Replaced {count} match(es){extra}.")
            return

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
        self._status.setText(f"Replaced {count} match(es).")

    def _selection_matches(self, cursor: QTextCursor, needle: str) -> bool:
        selected = cursor.selectedText().replace("\u2029", "\n")
        if self.case_box.isChecked():
            return selected == needle
        return selected.lower() == needle.lower()
