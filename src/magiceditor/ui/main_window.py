"""Primary application window shell."""

from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QMainWindow


class MainWindow(QMainWindow):
    """Top-level window: menus/toolbars/docks wired in later milestones."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MagicEditor")
        self.resize(1100, 720)
        placeholder = QLabel("MagicEditor — scaffold ready")
        placeholder.setStyleSheet("padding: 24px; font-size: 16px;")
        self.setCentralWidget(placeholder)
