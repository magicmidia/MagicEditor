"""Side-by-side plain text compare of two strings/paths."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)


class CompareDialog(QDialog):
    def __init__(
        self,
        left_title: str,
        left_text: str,
        right_title: str,
        right_text: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        title = "Compare"
        if parent is not None:
            tr = getattr(parent, "_tr", None)
            if tr is not None and hasattr(tr, "t"):
                title = tr.t("compare.title", title)
        self.setWindowTitle(title)
        self.resize(900, 560)
        self.setModal(True)

        left = QPlainTextEdit(self)
        left.setPlainText(left_text)
        left.setReadOnly(True)
        right = QPlainTextEdit(self)
        right.setPlainText(right_text)
        right.setReadOnly(True)

        row = QHBoxLayout()
        col_l = QVBoxLayout()
        col_l.addWidget(QLabel(left_title))
        col_l.addWidget(left, 1)
        col_r = QVBoxLayout()
        col_r.addWidget(QLabel(right_title))
        col_r.addWidget(right, 1)
        row.addLayout(col_l, 1)
        row.addLayout(col_r, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        buttons.clicked.connect(self.accept)

        root = QVBoxLayout(self)
        root.addLayout(row, 1)
        root.addWidget(buttons)

    @classmethod
    def from_paths(cls, left: Path, right: Path, parent: QWidget | None = None) -> CompareDialog:
        from magiceditor.services.compare_io import read_compare_text

        lt = read_compare_text(left)
        rt = read_compare_text(right)
        return cls(str(left), lt, str(right), rt, parent)
