"""Application bootstrap (Qt app + main window)."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from magiceditor.i18n.translator import TranslatorManager
from magiceditor.themes.manager import ThemeManager


def run(argv: Sequence[str] | None = None) -> int:
    """Start the Qt event loop. Returns process exit code."""
    args = list(argv if argv is not None else sys.argv)

    from PyQt6.QtWidgets import QApplication

    from magiceditor.ui.main_window import MainWindow

    app = QApplication(args)
    app.setApplicationName("MagicEditor")
    app.setOrganizationName("MagicEditor")
    app.setApplicationVersion("0.1.0")

    themes = ThemeManager()
    try:
        themes.apply(app, "midnight_dark")
    except (OSError, FileNotFoundError):
        pass

    translator = TranslatorManager()
    try:
        translator.load("en_US")
    except (OSError, FileNotFoundError):
        pass

    window = MainWindow(translator=translator, themes=themes)
    window.show()

    # Open files passed on the CLI
    for arg in args[1:]:
        if not arg.startswith("-"):
            window.open_path(arg)

    return app.exec()
