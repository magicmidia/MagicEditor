"""Command palette (Ctrl+Shift+P) — fuzzy filter over registered commands."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)


@dataclass
class PaletteCommand:
    id: str
    label: str
    callback: Callable[[], None]
    shortcut: str = ""


def _fuzzy_score(query: str, text: str) -> int:
    """Simple subsequence score; higher is better. -1 = no match."""
    if not query:
        return 0
    q = query.casefold()
    t = text.casefold()
    if q in t:
        return 1000 - t.index(q)
    qi = 0
    score = 0
    for ch in t:
        if qi < len(q) and ch == q[qi]:
            score += 10
            qi += 1
    return score if qi == len(q) else -1


class CommandPaletteDialog(QDialog):
    def __init__(
        self,
        commands: list[PaletteCommand],
        parent: QWidget | None = None,
        *,
        title: str = "Command Palette",
        placeholder: str = "Type a command…",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(520, 360)
        self._all = list(commands)
        self._run: PaletteCommand | None = None

        self.input = QLineEdit(self)
        self.input.setPlaceholderText(placeholder)
        self.list = QListWidget(self)
        hint = QLabel(self)
        hint.setObjectName("findDialogStatus")
        self._hint = hint

        lay = QVBoxLayout(self)
        lay.addWidget(self.input)
        lay.addWidget(self.list, 1)
        row = QHBoxLayout()
        row.addWidget(hint, 1)
        lay.addLayout(row)

        self.input.textChanged.connect(self._filter)
        self.list.itemActivated.connect(self._activate_item)
        QShortcut(QKeySequence("Return"), self, activated=self._accept_current)
        QShortcut(QKeySequence("Enter"), self, activated=self._accept_current)
        QShortcut(QKeySequence("Esc"), self, activated=self.reject)
        QShortcut(QKeySequence("Down"), self, activated=self._focus_list)

        self._filter("")
        self.input.setFocus()

    def _focus_list(self) -> None:
        self.list.setFocus()
        if self.list.count() and self.list.currentRow() < 0:
            self.list.setCurrentRow(0)

    def _filter(self, text: str) -> None:
        scored: list[tuple[int, PaletteCommand]] = []
        for cmd in self._all:
            s = _fuzzy_score(text, cmd.label + " " + cmd.id)
            if s >= 0:
                scored.append((s, cmd))
        scored.sort(key=lambda x: (-x[0], x[1].label.lower()))
        self.list.clear()
        for _s, cmd in scored[:80]:
            label = cmd.label
            if cmd.shortcut:
                label = f"{cmd.label}    ({cmd.shortcut})"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, cmd)
            self.list.addItem(item)
        if self.list.count():
            self.list.setCurrentRow(0)
        self._hint.setText(f"{self.list.count()} commands")

    def _activate_item(self, item: QListWidgetItem) -> None:
        cmd = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(cmd, PaletteCommand):
            self._run = cmd
            self.accept()

    def _accept_current(self) -> None:
        item = self.list.currentItem()
        if item is not None:
            self._activate_item(item)

    def selected_command(self) -> PaletteCommand | None:
        return self._run
