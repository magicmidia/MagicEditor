"""Simple document outline (Markdown headings / jump list)."""

from __future__ import annotations

import re
from typing import Any

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

_MD_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def extract_markdown_outline(text: str) -> list[tuple[int, int, str]]:
    """Return list of (1-based line, level, title)."""
    out: list[tuple[int, int, str]] = []
    for i, line in enumerate(text.splitlines(), start=1):
        m = _MD_HEADING.match(line)
        if m:
            out.append((i, len(m.group(1)), m.group(2).strip()))
    return out


class OutlineDialog(QDialog):
    """Jump to a heading in the current document."""

    line_chosen = pyqtSignal(int)

    def __init__(
        self,
        entries: list[tuple[int, int, str]],
        parent: QWidget | None = None,
        *,
        tr: Any | None = None,
    ) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setMinimumSize(360, 320)

        def t(key: str, default: str) -> str:
            return tr.t(key, default) if tr is not None else default

        self.setWindowTitle(t("outline.title", "Estrutura do documento"))
        self._list = QListWidget(self)
        for line, level, title in entries:
            indent = "  " * (level - 1)
            item = QListWidgetItem(f"{indent}{title}")
            item.setData(256, line)  # Qt.UserRole
            self._list.addItem(item)

        status = QLabel(
            t("outline.count", "{n} cabeçalho(s)").format(n=len(entries))
            if entries
            else t("outline.empty", "Nenhum cabeçalho Markdown encontrado."),
            self,
        )
        btn_go = QPushButton(t("goto.go", "Ir"), self)
        btn_go.setDefault(True)
        btn_go.clicked.connect(self._accept_current)
        btn_close = QPushButton(t("dialog.close", "Fechar"), self)
        btn_close.clicked.connect(self.reject)

        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(btn_go)
        row.addWidget(btn_close)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.addWidget(status)
        root.addWidget(self._list, 1)
        root.addLayout(row)

        self._list.itemDoubleClicked.connect(self._activate)
        self._list.itemActivated.connect(self._activate)
        QShortcut(QKeySequence("Esc"), self, activated=self.reject)
        if self._list.count() > 0:
            self._list.setCurrentRow(0)

    def _accept_current(self) -> None:
        self._activate(self._list.currentItem())

    def _activate(self, item: QListWidgetItem | None) -> None:
        if item is None:
            return
        line = item.data(256)
        if isinstance(line, int) and line > 0:
            self.line_chosen.emit(line)
            self.accept()
