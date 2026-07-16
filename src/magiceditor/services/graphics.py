"""GPU / rendering preferences (applied before or after QApplication)."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QSurfaceFormat
from PyQt6.QtWidgets import QApplication, QWidget


def configure_surface_before_app(*, gpu: bool = True, multisample: bool = True) -> None:
    """Call **before** constructing ``QApplication``.

    Enables OpenGL-backed composition and optional MSAA when ``gpu`` is True.
    Changing these attributes after QApplication exists has no effect (restart required).
    """
    if gpu:
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseDesktopOpenGL, True)
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)
        fmt = QSurfaceFormat()
        fmt.setRenderableType(QSurfaceFormat.RenderableType.OpenGL)
        fmt.setSwapBehavior(QSurfaceFormat.SwapBehavior.DoubleBuffer)
        fmt.setSwapInterval(1)  # vsync when available
        fmt.setSamples(4 if multisample else 0)
        fmt.setVersion(3, 3)
        fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
        QSurfaceFormat.setDefaultFormat(fmt)
    else:
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseSoftwareOpenGL, True)


def apply_window_opacity(window: QWidget, opacity: float) -> None:
    """Set whole-window opacity in ``[0.55, 1.0]``."""
    opacity = max(0.55, min(1.0, float(opacity)))
    window.setWindowOpacity(opacity)


def apply_translucent_chrome(window: QWidget, enabled: bool) -> None:
    """Hint translucent chrome (best-effort; pairs with opacity + QSS alphas)."""
    window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, enabled)
    window.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, enabled)


def graphics_status_summary(
    *,
    gpu: bool,
    multisample: bool,
    opacity: float,
    chrome_transparency: bool,
) -> str:
    pct = round(opacity * 100)
    parts = [
        "GPU " + ("ON" if gpu else "OFF"),
        "MSAA " + ("4x" if gpu and multisample else "off"),
        f"Opacity {pct}%",
    ]
    if chrome_transparency:
        parts.append("Glass chrome")
    return " · ".join(parts)
