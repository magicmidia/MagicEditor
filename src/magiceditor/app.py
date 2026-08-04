"""Application bootstrap (Qt app + splash + main window)."""

from __future__ import annotations

import sys
import time
from collections.abc import Sequence
from contextlib import suppress

from magiceditor.i18n.translator import TranslatorManager
from magiceditor.services.graphics import configure_surface_before_app
from magiceditor.services.settings import AppSettings
from magiceditor.themes.manager import ThemeManager
from magiceditor.version import APP_NAME, APP_ORG, SPLASH_MIN_SECONDS, version_display


def run(argv: Sequence[str] | None = None) -> int:
    """Start the Qt event loop. Returns process exit code."""
    args = list(argv if argv is not None else sys.argv)

    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QApplication

    from magiceditor.ui.fonts import load_bundled_fonts, ui_font
    from magiceditor.ui.main_window import MainWindow
    from magiceditor.ui.splash_screen import MagicSplash

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
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_ORG)
    app.setApplicationVersion(version_display())

    # Fusion gives consistent metrics; QSS layers the look.
    app.setStyle("Fusion")
    load_bundled_fonts()
    app.setFont(ui_font(10))

    # Application / taskbar icon (bundled multi-size .ico)
    with suppress(Exception):
        from magiceditor.ui.app_icon import load_app_icon

        icon = load_app_icon()
        if not icon.isNull():
            app.setWindowIcon(icon)

    settings = pre_settings
    session = pre_session

    show_splash = bool(getattr(session, "show_splash", True))
    splash: MagicSplash | None = None
    splash_t0 = time.monotonic()
    if show_splash:
        splash = MagicSplash()
        splash.set_message("Iniciando MagicEditor…")
        splash.show()
        app.processEvents()

    themes = ThemeManager()
    with suppress(OSError, FileNotFoundError):
        themes.apply(app, session.theme)
    if splash is not None:
        splash.set_message("Aplicando tema…")
        app.processEvents()

    translator = TranslatorManager()
    with suppress(OSError, FileNotFoundError):
        translator.load(session.language)
    if splash is not None:
        splash.set_message("Carregando interface…")
        app.processEvents()

    window = MainWindow(translator=translator, themes=themes, settings=settings)
    window.apply_graphics_preferences()
    if splash is not None:
        splash.set_message("Pronto")
        app.processEvents()
        # Guarantee minimum visibility (default 5s)
        remaining = SPLASH_MIN_SECONDS - (time.monotonic() - splash_t0)
        if remaining > 0:
            deadline = time.monotonic() + remaining
            while time.monotonic() < deadline:
                app.processEvents()
                time.sleep(0.016)
        splash.close()
        splash = None

    window.show()
    # First-run language/theme wizard (once) — after splash
    with suppress(Exception):
        window.maybe_show_first_run()

    # CLI files override / append to session
    for arg in args[1:]:
        if not arg.startswith("-"):
            window.open_path(arg)

    return app.exec()
