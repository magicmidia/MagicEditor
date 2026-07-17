"""Modern Phosphor/Lucide-style stroke icons (24×24 design grid).

Hand-drawn vector paths — no external icon font dependency.
Optical tuning: consistent stroke weight, 2px inset, HiDPI bitmaps.
"""

from __future__ import annotations

import math
from collections.abc import Callable

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

DrawFn = Callable[[QPainter], None]

# Visual weight for 20px toolbar (reads solid, not hairline)
_STROKE = 1.9
_INSET = 2.0  # design grid padding from 0..24 edges


def _pix(draw: DrawFn, color: str, size: int) -> QPixmap:
    # Render at 2× then scale for crisp edges
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    pen = QPen(QColor(color))
    pen.setWidthF(max(1.25, _STROKE * (size / 24.0)))
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
    for logical in (16, 18, 20, 22, 24, 28, 32):
        ico.addPixmap(_pix(draw, color, logical * 2))
    return ico


def toolbar_icon_color(theme_id: str) -> str:
    """Slightly brighter muted ink for legibility on dark chrome."""
    return {
        "luminous_void": "#D4D2D0",
        "clean_light": "#334155",
        "midnight_dark": "#A8B8CC",
        "darcula": "#A8B4C0",
        "cobalt_blue": "#B8D4F0",
        "monokai_pro": "#D0CED2",
    }.get(theme_id, "#94A3B8")


def accent_icon_color(theme_id: str) -> str:
    return {
        "luminous_void": "#FFD700",
        "clean_light": "#2563EB",
        "midnight_dark": "#22D3EE",
        "darcula": "#6897BB",
        "cobalt_blue": "#FFCC00",
        "monokai_pro": "#A9DC76",
    }.get(theme_id, "#FFD700")


def _draw_dot(p: QPainter) -> None:
    p.drawEllipse(QPointF(12, 12), 2.0, 2.0)


# --- file -----------------------------------------------------------------


def _draw_new(p: QPainter) -> None:
    # Document with folded corner + plus
    path = QPainterPath()
    path.moveTo(14, 3)
    path.lineTo(7, 3)
    path.cubicTo(5.9, 3, 5, 3.9, 5, 5)
    path.lineTo(5, 19)
    path.cubicTo(5, 20.1, 5.9, 21, 7, 21)
    path.lineTo(17, 21)
    path.cubicTo(18.1, 21, 19, 20.1, 19, 19)
    path.lineTo(19, 8)
    path.closeSubpath()
    p.drawPath(path)
    p.drawLine(QPointF(14, 3), QPointF(14, 8))
    p.drawLine(QPointF(14, 8), QPointF(19, 8))
    p.drawLine(QPointF(9.5, 13.5), QPointF(14.5, 13.5))
    p.drawLine(QPointF(12, 11), QPointF(12, 16))


def _draw_open(p: QPainter) -> None:
    # File with open corner (arrow out)
    path = QPainterPath()
    path.moveTo(13, 3)
    path.lineTo(7, 3)
    path.cubicTo(5.9, 3, 5, 3.9, 5, 5)
    path.lineTo(5, 19)
    path.cubicTo(5, 20.1, 5.9, 21, 7, 21)
    path.lineTo(17, 21)
    path.cubicTo(18.1, 21, 19, 20.1, 19, 19)
    path.lineTo(19, 11)
    p.drawPath(path)
    p.drawLine(QPointF(14, 3), QPointF(19, 8))
    p.drawLine(QPointF(14, 3), QPointF(14, 8))
    p.drawLine(QPointF(14, 8), QPointF(19, 8))
    # open arrow
    p.drawLine(QPointF(12, 14), QPointF(18, 14))
    p.drawLine(QPointF(15.5, 11.5), QPointF(18.5, 14.5))
    p.drawLine(QPointF(15.5, 16.5), QPointF(18.5, 14.5))


def _draw_folder(p: QPainter) -> None:
    path = QPainterPath()
    path.moveTo(3.5, 8)
    path.lineTo(3.5, 18)
    path.cubicTo(3.5, 19.1, 4.4, 20, 5.5, 20)
    path.lineTo(18.5, 20)
    path.cubicTo(19.6, 20, 20.5, 19.1, 20.5, 18)
    path.lineTo(20.5, 10)
    path.cubicTo(20.5, 8.9, 19.6, 8, 18.5, 8)
    path.lineTo(12, 8)
    path.lineTo(10.2, 5.8)
    path.lineTo(5.5, 5.8)
    path.cubicTo(4.4, 5.8, 3.5, 6.7, 3.5, 7.8)
    path.closeSubpath()
    p.drawPath(path)


def _draw_save(p: QPainter) -> None:
    path = QPainterPath()
    path.moveTo(5.5, 3.5)
    path.lineTo(15, 3.5)
    path.lineTo(20.5, 9)
    path.lineTo(20.5, 18.5)
    path.cubicTo(20.5, 19.6, 19.6, 20.5, 18.5, 20.5)
    path.lineTo(5.5, 20.5)
    path.cubicTo(4.4, 20.5, 3.5, 19.6, 3.5, 18.5)
    path.lineTo(3.5, 5.5)
    path.cubicTo(3.5, 4.4, 4.4, 3.5, 5.5, 3.5)
    path.closeSubpath()
    p.drawPath(path)
    p.drawRoundedRect(QRectF(7.5, 13.5, 9, 7), 1.2, 1.2)
    p.drawRoundedRect(QRectF(7.5, 3.5, 7.5, 5.5), 1, 1)


def _draw_save_as(p: QPainter) -> None:
    _draw_save(p)
    p.drawLine(QPointF(15, 12.5), QPointF(21, 18.5))
    p.drawLine(QPointF(17.5, 11), QPointF(22, 15.5))


def _draw_print(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(4, 9.5, 16, 8.5), 1.5, 1.5)
    path = QPainterPath()
    path.moveTo(7.5, 9.5)
    path.lineTo(7.5, 4)
    path.lineTo(16.5, 4)
    path.lineTo(16.5, 9.5)
    p.drawPath(path)
    p.drawRoundedRect(QRectF(7, 14.5, 10, 6.5), 1, 1)
    p.drawLine(QPointF(9, 17), QPointF(15, 17))
    p.drawLine(QPointF(9, 19), QPointF(13, 19))
    p.drawEllipse(QPointF(17.2, 12), 0.9, 0.9)


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
    p.drawLine(QPointF(8, 13.5), QPointF(16, 13.5))
    p.drawLine(QPointF(8, 16.5), QPointF(13.5, 16.5))


# --- clipboard ------------------------------------------------------------


def _draw_cut(p: QPainter) -> None:
    p.drawEllipse(QPointF(7, 7), 2.8, 2.8)
    p.drawEllipse(QPointF(7, 17), 2.8, 2.8)
    p.drawLine(QPointF(9.3, 8.6), QPointF(20, 18.5))
    p.drawLine(QPointF(9.3, 15.4), QPointF(20, 5.5))


def _draw_copy(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(8.5, 8, 11.5, 12.5), 1.5, 1.5)
    path = QPainterPath()
    path.moveTo(15.5, 8)
    path.lineTo(15.5, 5)
    path.cubicTo(15.5, 3.9, 14.6, 3, 13.5, 3)
    path.lineTo(5.5, 3)
    path.cubicTo(4.4, 3, 3.5, 3.9, 3.5, 5)
    path.lineTo(3.5, 14)
    path.cubicTo(3.5, 15.1, 4.4, 16, 5.5, 16)
    path.lineTo(8.5, 16)
    p.drawPath(path)


def _draw_paste(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(5, 5.5, 14, 15.5), 1.5, 1.5)
    p.drawRoundedRect(QRectF(8.5, 2.5, 7, 4.5), 1.2, 1.2)
    p.drawLine(QPointF(8.5, 12), QPointF(15.5, 12))
    p.drawLine(QPointF(8.5, 15.5), QPointF(13.5, 15.5))


def _draw_select_all(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(3.5, 3.5, 17, 17), 2, 2)
    p.drawLine(QPointF(7, 9), QPointF(17, 9))
    p.drawLine(QPointF(7, 12.5), QPointF(17, 12.5))
    p.drawLine(QPointF(7, 16), QPointF(14, 16))


# --- search / edit --------------------------------------------------------


def _draw_find(p: QPainter) -> None:
    p.drawEllipse(QPointF(10.5, 10.5), 5.9, 5.9)
    p.drawLine(QPointF(15, 15), QPointF(20.5, 20.5))


def _draw_find_files(p: QPainter) -> None:
    _draw_folder(p)
    p.drawEllipse(QPointF(16.8, 16), 3.0, 3.0)
    p.drawLine(QPointF(19, 18.2), QPointF(21.5, 20.5))


def _draw_quick_open(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(3, 5, 18, 14), 2.5, 2.5)
    p.drawEllipse(QPointF(10, 12), 3.3, 3.3)
    p.drawLine(QPointF(12.5, 14.5), QPointF(15.8, 17.5))
    p.drawLine(QPointF(16.5, 9), QPointF(19, 9))


def _draw_replace(p: QPainter) -> None:
    p.drawArc(QRectF(4, 5, 11, 11), 45 * 16, 240 * 16)
    p.drawLine(QPointF(13.8, 5), QPointF(16.5, 7.5))
    p.drawLine(QPointF(13.8, 5), QPointF(11, 7.2))
    p.drawArc(QRectF(9, 8, 11, 11), 225 * 16, 240 * 16)
    p.drawLine(QPointF(10.2, 19), QPointF(7.5, 16.5))
    p.drawLine(QPointF(10.2, 19), QPointF(13, 16.8))


def _draw_undo(p: QPainter) -> None:
    p.drawArc(QRectF(5, 6.5, 14, 11.5), 35 * 16, 210 * 16)
    p.drawLine(QPointF(6.2, 7.2), QPointF(4.5, 11.2))
    p.drawLine(QPointF(6.2, 7.2), QPointF(10, 8.5))


def _draw_redo(p: QPainter) -> None:
    p.drawArc(QRectF(5, 6.5, 14, 11.5), -35 * 16, -210 * 16)
    p.drawLine(QPointF(17.8, 7.2), QPointF(19.5, 11.2))
    p.drawLine(QPointF(17.8, 7.2), QPointF(14, 8.5))


def _draw_goto(p: QPainter) -> None:
    p.drawLine(QPointF(4, 12), QPointF(16.5, 12))
    p.drawLine(QPointF(13.5, 8.5), QPointF(18.5, 12))
    p.drawLine(QPointF(13.5, 15.5), QPointF(18.5, 12))
    p.drawLine(QPointF(6.5, 6.5), QPointF(6.5, 17.5))


def _draw_bookmark(p: QPainter) -> None:
    path = QPainterPath()
    path.moveTo(7, 3)
    path.lineTo(17, 3)
    path.lineTo(17, 20.5)
    path.lineTo(12, 16.8)
    path.lineTo(7, 20.5)
    path.closeSubpath()
    p.drawPath(path)


# --- view -----------------------------------------------------------------


def _draw_preview(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(3, 4, 8, 16), 1.5, 1.5)
    p.drawRoundedRect(QRectF(13, 4, 8, 16), 1.5, 1.5)
    p.drawLine(QPointF(5, 8), QPointF(9, 8))
    p.drawLine(QPointF(5, 11), QPointF(9, 11))
    p.drawLine(QPointF(5, 14), QPointF(8.5, 14))
    p.drawLine(QPointF(15, 9), QPointF(19, 9))
    p.drawLine(QPointF(15, 12), QPointF(18, 12))


def _draw_sidebar(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(3, 4, 18, 16), 2, 2)
    p.drawLine(QPointF(9.5, 4), QPointF(9.5, 20))
    p.drawLine(QPointF(5.2, 8), QPointF(7.8, 8))
    p.drawLine(QPointF(5.2, 11), QPointF(7.8, 11))
    p.drawLine(QPointF(5.2, 14), QPointF(7.8, 14))


def _draw_wrap(p: QPainter) -> None:
    p.drawLine(QPointF(4, 7), QPointF(15, 7))
    p.drawLine(QPointF(15, 7), QPointF(15, 11))
    p.drawLine(QPointF(15, 11), QPointF(8, 11))
    p.drawLine(QPointF(8, 11), QPointF(8, 15.5))
    p.drawLine(QPointF(8, 15.5), QPointF(18.5, 15.5))
    p.drawLine(QPointF(15.8, 13.3), QPointF(18.8, 15.5))
    p.drawLine(QPointF(15.8, 17.7), QPointF(18.8, 15.5))


def _draw_lines(p: QPainter) -> None:
    for y in (7.5, 12, 16.5):
        p.drawLine(QPointF(4, y), QPointF(7.8, y))
        p.drawLine(QPointF(10.5, y), QPointF(20, y))


def _draw_zoom_in(p: QPainter) -> None:
    p.drawEllipse(QPointF(10.5, 10.5), 5.9, 5.9)
    p.drawLine(QPointF(15, 15), QPointF(20.5, 20.5))
    p.drawLine(QPointF(8, 10.5), QPointF(13, 10.5))
    p.drawLine(QPointF(10.5, 8), QPointF(10.5, 13))


def _draw_zoom_out(p: QPainter) -> None:
    p.drawEllipse(QPointF(10.5, 10.5), 5.9, 5.9)
    p.drawLine(QPointF(15, 15), QPointF(20.5, 20.5))
    p.drawLine(QPointF(8, 10.5), QPointF(13, 10.5))


def _draw_zoom_reset(p: QPainter) -> None:
    p.drawEllipse(QPointF(11, 11), 6, 6)
    p.drawLine(QPointF(15.5, 15.5), QPointF(20.5, 20.5))
    p.drawLine(QPointF(11, 8.2), QPointF(11, 13.8))


def _draw_fullscreen(p: QPainter) -> None:
    for x0, y0, dx, dy in (
        (4, 4, 5.5, 0),
        (4, 4, 0, 5.5),
        (20, 4, -5.5, 0),
        (20, 4, 0, 5.5),
        (4, 20, 5.5, 0),
        (4, 20, 0, -5.5),
        (20, 20, -5.5, 0),
        (20, 20, 0, -5.5),
    ):
        p.drawLine(QPointF(x0, y0), QPointF(x0 + dx, y0 + dy))


def _draw_settings(p: QPainter) -> None:
    p.drawEllipse(QPointF(12, 12), 3.0, 3.0)
    for i in range(8):
        a = i * math.pi / 4
        p.drawLine(
            QPointF(12 + 5.5 * math.cos(a), 12 + 5.5 * math.sin(a)),
            QPointF(12 + 8.2 * math.cos(a), 12 + 8.2 * math.sin(a)),
        )


def _draw_exit(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(3, 4, 11, 16), 1.5, 1.5)
    p.drawLine(QPointF(12, 12), QPointF(21, 12))
    p.drawLine(QPointF(17.5, 8.5), QPointF(21, 12))
    p.drawLine(QPointF(17.5, 15.5), QPointF(21, 12))


def _draw_about(p: QPainter) -> None:
    p.drawEllipse(QPointF(12, 12), 8.2, 8.2)
    p.drawLine(QPointF(12, 10.8), QPointF(12, 16.8))
    p.drawEllipse(QPointF(12, 7.6), 0.7, 0.7)


def _draw_tab_close(p: QPainter) -> None:
    p.drawLine(QPointF(7.5, 7.5), QPointF(16.5, 16.5))
    p.drawLine(QPointF(16.5, 7.5), QPointF(7.5, 16.5))


def _draw_outline(p: QPainter) -> None:
    p.drawLine(QPointF(5, 7), QPointF(19, 7))
    p.drawLine(QPointF(7, 12), QPointF(17, 12))
    p.drawLine(QPointF(9, 17), QPointF(15, 17))


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
    "tab_close": _draw_tab_close,
    "outline": _draw_outline,
}
