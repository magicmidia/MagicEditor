"""Application bootstrap (Qt app + main window)."""

from __future__ import annotations

import sys
from collections.abc import Sequence


def run(argv: Sequence[str] | None = None) -> int:
    """Start the Qt event loop. Returns process exit code."""
    args = list(argv if argv is not None else sys.argv)

    from PyQt6.QtWidgets import QApplication

    from magiceditor.ui.main_window import MainWindow

    app = QApplication(args)
    app.setApplicationName("MagicEditor")
    app.setOrganizationName("MagicEditor")
    app.setApplicationVersion("0.1.0")

    window = MainWindow()
    window.show()
    return app.exec()
