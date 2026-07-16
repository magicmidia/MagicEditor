"""Polished stroke icons (Lucide-style 24x24 grid)."""

from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

DrawFn = Callable[[QPainter], None]

# Visual density tuned for 18-20px toolbar / 16px menus
_STROKE = 1.85


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
    for logical in (16, 18, 20, 24):
        ico.addPixmap(_pix(draw, color, logical * 2))
    return ico


def toolbar_icon_color(theme_id: str) -> str:
    """Muted ink that blends with chrome (not pure white / pure black)."""
    return {
        "clean_light": "#475569",
        "midnight_dark": "#94A3B8",
        "darcula": "#9AA7B5",
        "cobalt_blue": "#A8C8E8",
        "monokai_pro": "#C2C0C4",
    }.get(theme_id, "#94A3B8")


def _draw_dot(p: QPainter) -> None:
    p.drawEllipse(QPointF(12, 12), 2.2, 2.2)


def _draw_new(p: QPainter) -> None:
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
    p.drawLine(QPointF(9, 13), QPointF(15, 13))
    p.drawLine(QPointF(12, 10), QPointF(12, 16))


def _draw_open(p: QPainter) -> None:
    path = QPainterPath()
    path.moveTo(4, 20)
    path.lineTo(4, 8)
    path.cubicTo(4, 6.9, 4.9, 6, 6, 6)
    path.lineTo(9.5, 6)
    path.lineTo(11.5, 8.5)
    path.lineTo(18, 8.5)
    path.cubicTo(19.1, 8.5, 20, 9.4, 20, 10.5)
    path.lineTo(20, 20)
    path.cubicTo(20, 21.1, 19.1, 22, 18, 22)
    path.lineTo(6, 22)
    path.cubicTo(4.9, 22, 4, 21.1, 4, 20)
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
    p.drawRoundedRect(QRectF(7, 13, 10, 8), 1, 1)
    p.drawRoundedRect(QRectF(7, 3, 8, 6), 1, 1)


def _draw_save_as(p: QPainter) -> None:
    _draw_save(p)
    p.drawLine(QPointF(16, 14), QPointF(21, 19))
    p.drawLine(QPointF(18, 12), QPointF(22, 16))


def _draw_find(p: QPainter) -> None:
    p.drawEllipse(QPointF(10.5, 10.5), 5.75, 5.75)
    p.drawLine(QPointF(14.8, 14.8), QPointF(20.5, 20.5))


def _draw_replace(p: QPainter) -> None:
    # two arrows cycle
    p.drawArc(QRectF(4, 5, 11, 11), 50 * 16, 230 * 16)
    p.drawLine(QPointF(13.5, 5.2), QPointF(16.2, 7.8))
    p.drawLine(QPointF(13.5, 5.2), QPointF(10.8, 7.5))
    p.drawArc(QRectF(9, 8, 11, 11), 230 * 16, 230 * 16)
    p.drawLine(QPointF(10.5, 18.8), QPointF(7.8, 16.2))
    p.drawLine(QPointF(10.5, 18.8), QPointF(13.2, 16.5))


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
    p.drawEllipse(QPointF(10.5, 10.5), 5.75, 5.75)
    p.drawLine(QPointF(14.8, 14.8), QPointF(20.5, 20.5))
    p.drawLine(QPointF(8, 10.5), QPointF(13, 10.5))
    p.drawLine(QPointF(10.5, 8), QPointF(10.5, 13))


def _draw_zoom_out(p: QPainter) -> None:
    p.drawEllipse(QPointF(10.5, 10.5), 5.75, 5.75)
    p.drawLine(QPointF(14.8, 14.8), QPointF(20.5, 20.5))
    p.drawLine(QPointF(8, 10.5), QPointF(13, 10.5))


def _draw_zoom_reset(p: QPainter) -> None:
    p.drawEllipse(QPointF(11, 11), 6, 6)
    p.drawLine(QPointF(15.5, 15.5), QPointF(20.5, 20.5))
    p.drawLine(QPointF(11, 8.2), QPointF(11, 13.8))


def _draw_fullscreen(p: QPainter) -> None:
    # four corner brackets
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


def _draw_exit(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(3, 4, 11, 16), 1.2, 1.2)
    p.drawLine(QPointF(12, 12), QPointF(21, 12))
    p.drawLine(QPointF(17.5, 8.5), QPointF(21, 12))
    p.drawLine(QPointF(17.5, 15.5), QPointF(21, 12))


def _draw_about(p: QPainter) -> None:
    p.drawEllipse(QPointF(12, 12), 8, 8)
    p.drawLine(QPointF(12, 10.5), QPointF(12, 16.5))
    p.drawEllipse(QPointF(12, 7.8), 0.6, 0.6)


_DRAWERS: dict[str, DrawFn] = {
    "new": _draw_new,
    "open": _draw_open,
    "folder": _draw_folder,
    "save": _draw_save,
    "save_as": _draw_save_as,
    "find": _draw_find,
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
}
