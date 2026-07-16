"""Application bootstrap (Qt app + main window)."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from contextlib import suppress

from magiceditor.i18n.translator import TranslatorManager
from magiceditor.services.graphics import configure_surface_before_app
from magiceditor.services.settings import AppSettings
from magiceditor.themes.manager import ThemeManager


def run(argv: Sequence[str] | None = None) -> int:
    """Start the Qt event loop. Returns process exit code."""
    args = list(argv if argv is not None else sys.argv)

    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QApplication

    from magiceditor.ui.fonts import load_bundled_fonts, ui_font
    from magiceditor.ui.main_window import MainWindow

    # Peek graphics prefs before QApplication (GPU surface format).
    pre_settings = AppSettings()
    pre_session = pre_settings.load()
    configure_surface_before_app(
        gpu=pre_session.gpu_acceleration,
        multisample=pre_session.gpu_multisample,
    )

    # High-DPI before QApplication
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(args)
    app.setApplicationName("MagicEditor")
    app.setOrganizationName("MagicEditor")
    app.setApplicationVersion("0.1.0")

    # Fusion gives consistent metrics; QSS layers the look.
    app.setStyle("Fusion")
    load_bundled_fonts()
    app.setFont(ui_font(10))

    settings = pre_settings
    session = pre_session

    themes = ThemeManager()
    with suppress(OSError, FileNotFoundError):
        themes.apply(app, session.theme)

    translator = TranslatorManager()
    with suppress(OSError, FileNotFoundError):
        translator.load(session.language)

    window = MainWindow(translator=translator, themes=themes, settings=settings)
    window.apply_graphics_preferences()
    window.show()

    # CLI files override / append to session
    for arg in args[1:]:
        if not arg.startswith("-"):
            window.open_path(arg)

    return app.exec()
