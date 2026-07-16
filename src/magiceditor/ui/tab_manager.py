"""Tab widget with planned middle-click close and tear-off support."""

from __future__ import annotations

from PyQt6.QtWidgets import QTabWidget


class TabManager(QTabWidget):
    """Extended tab bar for multi-document editing."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)
