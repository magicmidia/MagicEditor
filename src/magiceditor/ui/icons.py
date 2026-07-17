"""Modern Lucide-inspired stroke icons (24×24 design grid).

Hand-drawn vector paths keep the binary free of icon font packages while
matching current IDE chrome density (20px toolbar, 16–18px menus).
"""

from __future__ import annotations

import math
from collections.abc import Callable

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

DrawFn = Callable[[QPainter], None]

# Optical weight for 20px toolbar / 2× retina pixmaps
_STROKE = 1.7


def _pix(draw: DrawFn, color: str, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    pen = QPen(QColor(color))
    pen.setWidthF(_STROKE * (size / 24.0))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    scale = size / 24.0
    p.scale(scale, scale)
    draw(p)
    p.end()
    return pm


def icon(name: str, color: str = "#94A3B8") -> QIcon:
    draw = _DRAWERS.get(name, _draw_dot)
    ico = QIcon()
    # @2x bitmaps for crisp HiDPI toolbars
    for logical in (16, 18, 20, 24):
        ico.addPixmap(_pix(draw, color, logical * 2))
    return ico


def toolbar_icon_color(theme_id: str) -> str:
    """Muted ink that blends with chrome (not pure white / pure black)."""
    return {
        "luminous_void": "#C8C6C5",
        "clean_light": "#475569",
        "midnight_dark": "#94A3B8",
        "darcula": "#9AA7B5",
        "cobalt_blue": "#A8C8E8",
        "monokai_pro": "#C2C0C4",
    }.get(theme_id, "#94A3B8")


def _draw_dot(p: QPainter) -> None:
    p.drawEllipse(QPointF(12, 12), 2.0, 2.0)


# --- file ---------------------------------------------------------------


def _draw_new(p: QPainter) -> None:
    path = QPainterPath()
    path.moveTo(14, 2.5)
    path.lineTo(7, 2.5)
    path.cubicTo(5.9, 2.5, 5, 3.4, 5, 4.5)
    path.lineTo(5, 19.5)
    path.cubicTo(5, 20.6, 5.9, 21.5, 7, 21.5)
    path.lineTo(17, 21.5)
    path.cubicTo(18.1, 21.5, 19, 20.6, 19, 19.5)
    path.lineTo(19, 7.5)
    path.closeSubpath()
    p.drawPath(path)
    p.drawLine(QPointF(14, 2.5), QPointF(14, 7.5))
    p.drawLine(QPointF(14, 7.5), QPointF(19, 7.5))
    p.drawLine(QPointF(9, 13.5), QPointF(15, 13.5))
    p.drawLine(QPointF(12, 10.5), QPointF(12, 16.5))


def _draw_open(p: QPainter) -> None:
    path = QPainterPath()
    path.moveTo(3.5, 19.5)
    path.lineTo(3.5, 7.5)
    path.cubicTo(3.5, 6.4, 4.4, 5.5, 5.5, 5.5)
    path.lineTo(9.2, 5.5)
    path.lineTo(11.2, 8)
    path.lineTo(18.5, 8)
    path.cubicTo(19.6, 8, 20.5, 8.9, 20.5, 10)
    path.lineTo(20.5, 19.5)
    path.cubicTo(20.5, 20.6, 19.6, 21.5, 18.5, 21.5)
    path.lineTo(5.5, 21.5)
    path.cubicTo(4.4, 21.5, 3.5, 20.6, 3.5, 19.5)
    path.closeSubpath()
    p.drawPath(path)


def _draw_folder(p: QPainter) -> None:
    path = QPainterPath()
    path.moveTo(3, 7)
    path.lineTo(3, 18)
    path.cubicTo(3, 19.1, 3.9, 20, 5, 20)
    path.lineTo(19, 20)
    path.cubicTo(20.1, 20, 21, 19.1, 21, 18)
    path.lineTo(21, 9)
    path.cubicTo(21, 7.9, 20.1, 7, 19, 7)
    path.lineTo(12, 7)
    path.lineTo(10, 5)
    path.lineTo(5, 5)
    path.cubicTo(3.9, 5, 3, 5.9, 3, 7)
    path.closeSubpath()
    p.drawPath(path)


def _draw_save(p: QPainter) -> None:
    path = QPainterPath()
    path.moveTo(5, 3)
    path.lineTo(15, 3)
    path.lineTo(21, 9)
    path.lineTo(21, 19)
    path.cubicTo(21, 20.1, 20.1, 21, 19, 21)
    path.lineTo(5, 21)
    path.cubicTo(3.9, 21, 3, 20.1, 3, 19)
    path.lineTo(3, 5)
    path.cubicTo(3, 3.9, 3.9, 3, 5, 3)
    path.closeSubpath()
    p.drawPath(path)
    p.drawRoundedRect(QRectF(7, 13, 10, 8), 1.2, 1.2)
    p.drawRoundedRect(QRectF(7, 3, 8, 6), 1.2, 1.2)


def _draw_save_as(p: QPainter) -> None:
    _draw_save(p)
    p.drawLine(QPointF(15.5, 13.5), QPointF(21, 19))
    p.drawLine(QPointF(17.5, 12), QPointF(22, 16.5))


def _draw_print(p: QPainter) -> None:
    # Printer body + paper (Lucide-style)
    p.drawRoundedRect(QRectF(4, 9, 16, 9), 1.5, 1.5)
    path = QPainterPath()
    path.moveTo(7, 9)
    path.lineTo(7, 4)
    path.lineTo(17, 4)
    path.lineTo(17, 9)
    p.drawPath(path)
    p.drawRoundedRect(QRectF(7, 14, 10, 7), 1, 1)
    p.drawLine(QPointF(9, 16.5), QPointF(15, 16.5))
    p.drawLine(QPointF(9, 18.5), QPointF(13, 18.5))
    p.drawEllipse(QPointF(17.5, 11.5), 1.0, 1.0)


def _draw_export_pdf(p: QPainter) -> None:
    path = QPainterPath()
    path.moveTo(13, 3)
    path.lineTo(7, 3)
    path.cubicTo(5.9, 3, 5, 3.9, 5, 5)
    path.lineTo(5, 19)
    path.cubicTo(5, 20.1, 5.9, 21, 7, 21)
    path.lineTo(17, 21)
    path.cubicTo(18.1, 21, 19, 20.1, 19, 19)
    path.lineTo(19, 9)
    path.closeSubpath()
    p.drawPath(path)
    p.drawLine(QPointF(13, 3), QPointF(13, 9))
    p.drawLine(QPointF(13, 9), QPointF(19, 9))
    p.drawLine(QPointF(8, 14), QPointF(16, 14))
    p.drawLine(QPointF(8, 17), QPointF(14, 17))


# --- clipboard ----------------------------------------------------------


def _draw_cut(p: QPainter) -> None:
    # Scissors (Lucide-style)
    p.drawEllipse(QPointF(7, 7), 2.6, 2.6)
    p.drawEllipse(QPointF(7, 17), 2.6, 2.6)
    p.drawLine(QPointF(9.2, 8.5), QPointF(20, 18))
    p.drawLine(QPointF(9.2, 15.5), QPointF(20, 6))
    p.drawLine(QPointF(12, 12), QPointF(9.5, 12))


def _draw_copy(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(8, 8, 12, 13), 1.5, 1.5)
    path = QPainterPath()
    path.moveTo(16, 8)
    path.lineTo(16, 5)
    path.cubicTo(16, 3.9, 15.1, 3, 14, 3)
    path.lineTo(5, 3)
    path.cubicTo(3.9, 3, 3, 3.9, 3, 5)
    path.lineTo(3, 14)
    path.cubicTo(3, 15.1, 3.9, 16, 5, 16)
    path.lineTo(8, 16)
    p.drawPath(path)


def _draw_paste(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(5, 5, 14, 16), 1.5, 1.5)
    p.drawRoundedRect(QRectF(8.5, 2.5, 7, 4.5), 1.2, 1.2)
    p.drawLine(QPointF(8, 12), QPointF(16, 12))
    p.drawLine(QPointF(8, 15.5), QPointF(14, 15.5))


def _draw_select_all(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(3.5, 3.5, 17, 17), 1.5, 1.5)
    p.drawLine(QPointF(7, 9), QPointF(17, 9))
    p.drawLine(QPointF(7, 12.5), QPointF(17, 12.5))
    p.drawLine(QPointF(7, 16), QPointF(14, 16))


# --- edit / search ------------------------------------------------------


def _draw_find(p: QPainter) -> None:
    p.drawEllipse(QPointF(10.5, 10.5), 5.8, 5.8)
    p.drawLine(QPointF(14.9, 14.9), QPointF(20.5, 20.5))


def _draw_find_files(p: QPainter) -> None:
    _draw_folder(p)
    # mini magnifier
    p.drawEllipse(QPointF(16.5, 15.5), 3.2, 3.2)
    p.drawLine(QPointF(18.8, 17.8), QPointF(21.5, 20.5))


def _draw_quick_open(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(3, 5, 18, 14), 2, 2)
    p.drawEllipse(QPointF(10, 12), 3.2, 3.2)
    p.drawLine(QPointF(12.4, 14.4), QPointF(15.5, 17.5))
    p.drawLine(QPointF(16, 9), QPointF(19, 9))


def _draw_replace(p: QPainter) -> None:
    p.drawArc(QRectF(4, 5, 11, 11), 50 * 16, 230 * 16)
    p.drawLine(QPointF(13.5, 5.2), QPointF(16.2, 7.8))
    p.drawLine(QPointF(13.5, 5.2), QPointF(10.8, 7.5))
    p.drawArc(QRectF(9, 8, 11, 11), 230 * 16, 230 * 16)
    p.drawLine(QPointF(10.5, 18.8), QPointF(7.8, 16.2))
    p.drawLine(QPointF(10.5, 18.8), QPointF(13.2, 16.5))


def _draw_undo(p: QPainter) -> None:
    p.drawArc(QRectF(5, 6, 14, 12), 40 * 16, 200 * 16)
    p.drawLine(QPointF(6.5, 7), QPointF(5, 11))
    p.drawLine(QPointF(6.5, 7), QPointF(10, 8.5))


def _draw_redo(p: QPainter) -> None:
    p.drawArc(QRectF(5, 6, 14, 12), -40 * 16, -200 * 16)
    p.drawLine(QPointF(17.5, 7), QPointF(19, 11))
    p.drawLine(QPointF(17.5, 7), QPointF(14, 8.5))


def _draw_goto(p: QPainter) -> None:
    p.drawLine(QPointF(4, 12), QPointF(16, 12))
    p.drawLine(QPointF(13, 8), QPointF(18, 12))
    p.drawLine(QPointF(13, 16), QPointF(18, 12))
    p.drawLine(QPointF(6, 6), QPointF(6, 18))


def _draw_bookmark(p: QPainter) -> None:
    path = QPainterPath()
    path.moveTo(7, 3)
    path.lineTo(17, 3)
    path.lineTo(17, 20.5)
    path.lineTo(12, 16.5)
    path.lineTo(7, 20.5)
    path.closeSubpath()
    p.drawPath(path)


# --- view ---------------------------------------------------------------


def _draw_preview(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(3, 4, 8, 16), 1.2, 1.2)
    p.drawRoundedRect(QRectF(13, 4, 8, 16), 1.2, 1.2)
    p.drawLine(QPointF(5, 8), QPointF(9, 8))
    p.drawLine(QPointF(5, 11), QPointF(9, 11))
    p.drawLine(QPointF(5, 14), QPointF(8, 14))


def _draw_sidebar(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(3, 4, 18, 16), 1.5, 1.5)
    p.drawLine(QPointF(9, 4), QPointF(9, 20))
    p.drawLine(QPointF(5, 8), QPointF(7.5, 8))
    p.drawLine(QPointF(5, 11), QPointF(7.5, 11))
    p.drawLine(QPointF(5, 14), QPointF(7.5, 14))


def _draw_wrap(p: QPainter) -> None:
    p.drawLine(QPointF(4, 7), QPointF(15, 7))
    p.drawLine(QPointF(15, 7), QPointF(15, 11))
    p.drawLine(QPointF(15, 11), QPointF(8, 11))
    p.drawLine(QPointF(8, 11), QPointF(8, 15))
    p.drawLine(QPointF(8, 15), QPointF(18, 15))
    p.drawLine(QPointF(15.5, 13), QPointF(18.5, 15))
    p.drawLine(QPointF(15.5, 17), QPointF(18.5, 15))


def _draw_lines(p: QPainter) -> None:
    for y in (7, 12, 17):
        p.drawLine(QPointF(4, y), QPointF(7.5, y))
        p.drawLine(QPointF(10.5, y), QPointF(20, y))


def _draw_zoom_in(p: QPainter) -> None:
    p.drawEllipse(QPointF(10.5, 10.5), 5.8, 5.8)
    p.drawLine(QPointF(14.9, 14.9), QPointF(20.5, 20.5))
    p.drawLine(QPointF(8, 10.5), QPointF(13, 10.5))
    p.drawLine(QPointF(10.5, 8), QPointF(10.5, 13))


def _draw_zoom_out(p: QPainter) -> None:
    p.drawEllipse(QPointF(10.5, 10.5), 5.8, 5.8)
    p.drawLine(QPointF(14.9, 14.9), QPointF(20.5, 20.5))
    p.drawLine(QPointF(8, 10.5), QPointF(13, 10.5))


def _draw_zoom_reset(p: QPainter) -> None:
    p.drawEllipse(QPointF(11, 11), 6, 6)
    p.drawLine(QPointF(15.5, 15.5), QPointF(20.5, 20.5))
    p.drawLine(QPointF(11, 8.2), QPointF(11, 13.8))


def _draw_fullscreen(p: QPainter) -> None:
    for x0, y0, dx, dy in (
        (4, 4, 5, 0),
        (4, 4, 0, 5),
        (20, 4, -5, 0),
        (20, 4, 0, 5),
        (4, 20, 5, 0),
        (4, 20, 0, -5),
        (20, 20, -5, 0),
        (20, 20, 0, -5),
    ):
        p.drawLine(QPointF(x0, y0), QPointF(x0 + dx, y0 + dy))


def _draw_settings(p: QPainter) -> None:
    p.drawEllipse(QPointF(12, 12), 3.0, 3.0)
    for i in range(8):
        a = i * math.pi / 4
        p.drawLine(
            QPointF(12 + 5.4 * math.cos(a), 12 + 5.4 * math.sin(a)),
            QPointF(12 + 8.0 * math.cos(a), 12 + 8.0 * math.sin(a)),
        )


def _draw_exit(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(3, 4, 11, 16), 1.2, 1.2)
    p.drawLine(QPointF(12, 12), QPointF(21, 12))
    p.drawLine(QPointF(17.5, 8.5), QPointF(21, 12))
    p.drawLine(QPointF(17.5, 15.5), QPointF(21, 12))


def _draw_about(p: QPainter) -> None:
    p.drawEllipse(QPointF(12, 12), 8, 8)
    p.drawLine(QPointF(12, 10.5), QPointF(12, 16.5))
    p.drawEllipse(QPointF(12, 7.8), 0.55, 0.55)


_DRAWERS: dict[str, DrawFn] = {
    "new": _draw_new,
    "open": _draw_open,
    "folder": _draw_folder,
    "save": _draw_save,
    "save_as": _draw_save_as,
    "print": _draw_print,
    "export_pdf": _draw_export_pdf,
    "cut": _draw_cut,
    "copy": _draw_copy,
    "paste": _draw_paste,
    "select_all": _draw_select_all,
    "find": _draw_find,
    "find_files": _draw_find_files,
    "quick_open": _draw_quick_open,
    "replace": _draw_replace,
    "preview": _draw_preview,
    "sidebar": _draw_sidebar,
    "wrap": _draw_wrap,
    "lines": _draw_lines,
    "zoom_in": _draw_zoom_in,
    "zoom_out": _draw_zoom_out,
    "zoom_reset": _draw_zoom_reset,
    "fullscreen": _draw_fullscreen,
    "exit": _draw_exit,
    "about": _draw_about,
    "undo": _draw_undo,
    "redo": _draw_redo,
    "settings": _draw_settings,
    "bookmark": _draw_bookmark,
    "goto": _draw_goto,
}
