"""Unified Goto Anything: file path, :line, #heading / @symbol."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)


@dataclass
class GotoTarget:
    kind: str  # file | line | symbol
    label: str
    path: str | None = None
    line: int | None = None  # 1-based


class GotoAnythingDialog(QDialog):
    def __init__(
        self,
        *,
        files: list[str],
        symbols: list[tuple[str, int]],  # name, line 1-based
        parent: QWidget | None = None,
        on_accept: Callable[[GotoTarget], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Go to Anything")
        self.setModal(True)
        self.resize(520, 380)
        self._files = files
        self._symbols = symbols
        self._on_accept = on_accept
        self._chosen: GotoTarget | None = None

        self.input = QLineEdit(self)
        self.input.setPlaceholderText("file · :line · #heading · @symbol")
        self.list = QListWidget(self)

        root = QVBoxLayout(self)
        root.addWidget(self.input)
        root.addWidget(self.list, 1)

        self.input.textChanged.connect(self._filter)
        self.list.itemActivated.connect(self._activate)
        QShortcut(QKeySequence("Return"), self, activated=self._accept_current)
        QShortcut(QKeySequence("Esc"), self, activated=self.reject)
        self._filter("")
        self.input.setFocus()

    def _filter(self, text: str) -> None:
        self.list.clear()
        q = text.strip()
        items: list[GotoTarget] = []

        if q.startswith(":"):
            try:
                line = int(q[1:].strip() or "1")
                items.append(GotoTarget(kind="line", label=f"Line {line}", line=line))
            except ValueError:
                pass
        elif q.startswith("#") or q.startswith("@"):
            needle = q[1:].casefold()
            for name, line in self._symbols:
                if not needle or needle in name.casefold():
                    items.append(GotoTarget(kind="symbol", label=f"{name}  :{line}", line=line))
        else:
            needle = q.casefold()
            for p in self._files:
                name = Path(p).name
                if not needle or needle in name.casefold() or needle in p.casefold():
                    items.append(GotoTarget(kind="file", label=p, path=p))
            # also allow :line suffix file:12
            if ":" in q and not q.startswith(":"):
                left, _, right = q.rpartition(":")
                if right.isdigit():
                    items.insert(
                        0,
                        GotoTarget(
                            kind="line",
                            label=f"{left} → line {right}",
                            path=left if left else None,
                            line=int(right),
                        ),
                    )

        for tgt in items[:100]:
            it = QListWidgetItem(tgt.label)
            it.setData(Qt.ItemDataRole.UserRole, tgt)
            self.list.addItem(it)
        if self.list.count():
            self.list.setCurrentRow(0)

    def _activate(self, item: QListWidgetItem) -> None:
        tgt = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(tgt, GotoTarget):
            self._chosen = tgt
            if self._on_accept:
                self._on_accept(tgt)
            self.accept()

    def _accept_current(self) -> None:
        item = self.list.currentItem()
        if item is not None:
            self._activate(item)

    def chosen(self) -> GotoTarget | None:
        return self._chosen
