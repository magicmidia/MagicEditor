"""Go to Line modal dialog."""

from __future__ import annotations

from PyQt6.QtGui import QIntValidator, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class GoToLineDialog(QDialog):
    """Ask for a 1-based line number within ``1..max_line``."""

    def __init__(
        self,
        max_line: int,
        current_line: int = 1,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._max = max(1, max_line)
        self.setModal(True)
        self.setWindowTitle("Go to Line")
        self.setMinimumWidth(320)
        self.setObjectName("gotoLineDialog")

        self._input = QLineEdit(self)
        self._input.setValidator(QIntValidator(1, self._max, self))
        self._input.setText(str(max(1, min(self._max, current_line))))
        self._input.selectAll()

        self._status = QLabel(f"Line (1-{self._max})", self)
        self._status.setObjectName("findDialogStatus")

        btn_go = QPushButton("Go", self)
        btn_go.setDefault(True)
        btn_go.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancel", self)
        btn_cancel.clicked.connect(self.reject)

        row = QHBoxLayout()
        row.addWidget(QLabel("Line:", self))
        row.addWidget(self._input, 1)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(btn_go)
        buttons.addWidget(btn_cancel)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)
        root.addLayout(row)
        root.addWidget(self._status)
        root.addLayout(buttons)

        self._input.returnPressed.connect(self.accept)
        QShortcut(QKeySequence("Esc"), self, activated=self.reject)
        self._input.setFocus()

    def line_number(self) -> int:
        """Return 1-based line, clamped to valid range."""
        try:
            n = int(self._input.text().strip() or "1")
        except ValueError:
            n = 1
        return max(1, min(self._max, n))
