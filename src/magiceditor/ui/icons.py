"""Modern monochrome icons drawn with QPainter (no external assets)."""

from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

DrawFn = Callable[[QPainter, QColor], None]


def _pix(draw: DrawFn, color: str, size: int = 64) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    pen = QPen(QColor(color))
    pen.setWidthF(size * 0.07)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # normalize to 24x24 canvas
    scale = size / 24.0
    p.scale(scale, scale)
    draw(p, QColor(color))
    p.end()
    return pm


def icon(name: str, color: str = "#E2E8F0") -> QIcon:
    draw = _DRAWERS.get(name, _draw_dot)
    ico = QIcon()
    for sz in (16, 20, 24, 32, 48):
        ico.addPixmap(_pix(draw, color, sz * 2))
    return ico


def _draw_dot(p: QPainter, c: QColor) -> None:
    p.setBrush(c)
    p.drawEllipse(QPointF(12, 12), 3, 3)


def _draw_new(p: QPainter, _c: QColor) -> None:
    p.drawRoundedRect(QRectF(5, 3, 12, 16), 1.5, 1.5)
    p.drawLine(QPointF(9, 12), QPointF(15, 12))
    p.drawLine(QPointF(12, 9), QPointF(12, 15))


def _draw_open(p: QPainter, _c: QColor) -> None:
    path = QPainterPath()
    path.moveTo(3, 8)
    path.lineTo(3, 19)
    path.lineTo(21, 19)
    path.lineTo(21, 8)
    path.lineTo(12, 8)
    path.lineTo(10, 5)
    path.lineTo(3, 5)
    path.closeSubpath()
    p.drawPath(path)


def _draw_folder(p: QPainter, _c: QColor) -> None:
    path = QPainterPath()
    path.moveTo(3, 7)
    path.lineTo(3, 19)
    path.lineTo(21, 19)
    path.lineTo(21, 9)
    path.lineTo(12, 9)
    path.lineTo(10, 6)
    path.lineTo(3, 6)
    path.closeSubpath()
    p.drawPath(path)


def _draw_save(p: QPainter, _c: QColor) -> None:
    path = QPainterPath()
    path.moveTo(5, 3)
    path.lineTo(16, 3)
    path.lineTo(21, 8)
    path.lineTo(21, 21)
    path.lineTo(5, 21)
    path.closeSubpath()
    p.drawPath(path)
    p.drawRect(QRectF(8, 13, 8, 8))
    p.drawRect(QRectF(8, 3, 7, 6))


def _draw_save_as(p: QPainter, c: QColor) -> None:
    _draw_save(p, c)
    p.drawLine(QPointF(17, 14), QPointF(21, 18))
    p.drawLine(QPointF(19, 12), QPointF(22, 15))


def _draw_find(p: QPainter, _c: QColor) -> None:
    p.drawEllipse(QPointF(10, 10), 5.5, 5.5)
    p.drawLine(QPointF(14.5, 14.5), QPointF(20, 20))


def _draw_replace(p: QPainter, _c: QColor) -> None:
    p.drawArc(QRectF(4, 5, 10, 10), 40 * 16, 240 * 16)
    p.drawLine(QPointF(12, 5), QPointF(15, 8))
    p.drawLine(QPointF(12, 5), QPointF(9, 8))
    p.drawArc(QRectF(10, 9, 10, 10), 220 * 16, 240 * 16)
    p.drawLine(QPointF(12, 19), QPointF(9, 16))
    p.drawLine(QPointF(12, 19), QPointF(15, 16))


def _draw_preview(p: QPainter, _c: QColor) -> None:
    p.drawRoundedRect(QRectF(3, 5, 8, 14), 1, 1)
    p.drawRoundedRect(QRectF(13, 5, 8, 14), 1, 1)
    p.drawLine(QPointF(5, 9), QPointF(9, 9))
    p.drawLine(QPointF(5, 12), QPointF(9, 12))


def _draw_sidebar(p: QPainter, _c: QColor) -> None:
    p.drawRoundedRect(QRectF(3, 4, 18, 16), 1.5, 1.5)
    p.drawLine(QPointF(9, 4), QPointF(9, 20))


def _draw_wrap(p: QPainter, _c: QColor) -> None:
    p.drawLine(QPointF(4, 7), QPointF(16, 7))
    p.drawLine(QPointF(16, 7), QPointF(16, 11))
    p.drawLine(QPointF(16, 11), QPointF(8, 11))
    p.drawLine(QPointF(8, 11), QPointF(8, 15))
    p.drawLine(QPointF(8, 15), QPointF(18, 15))
    p.drawLine(QPointF(15, 13), QPointF(18, 15))
    p.drawLine(QPointF(15, 17), QPointF(18, 15))


def _draw_lines(p: QPainter, _c: QColor) -> None:
    p.drawLine(QPointF(4, 6), QPointF(8, 6))
    p.drawLine(QPointF(11, 6), QPointF(20, 6))
    p.drawLine(QPointF(4, 12), QPointF(8, 12))
    p.drawLine(QPointF(11, 12), QPointF(20, 12))
    p.drawLine(QPointF(4, 18), QPointF(8, 18))
    p.drawLine(QPointF(11, 18), QPointF(20, 18))


def _draw_zoom_in(p: QPainter, _c: QColor) -> None:
    p.drawEllipse(QPointF(10, 10), 5.5, 5.5)
    p.drawLine(QPointF(14.5, 14.5), QPointF(20, 20))
    p.drawLine(QPointF(7.5, 10), QPointF(12.5, 10))
    p.drawLine(QPointF(10, 7.5), QPointF(10, 12.5))


def _draw_zoom_out(p: QPainter, _c: QColor) -> None:
    p.drawEllipse(QPointF(10, 10), 5.5, 5.5)
    p.drawLine(QPointF(14.5, 14.5), QPointF(20, 20))
    p.drawLine(QPointF(7.5, 10), QPointF(12.5, 10))


def _draw_zoom_reset(p: QPainter, c: QColor) -> None:
    p.drawEllipse(QPointF(11, 11), 6, 6)
    p.drawLine(QPointF(15.5, 15.5), QPointF(20, 20))
    # small "1x" mark
    p.drawLine(QPointF(11, 8.5), QPointF(11, 13.5))


def _draw_fullscreen(p: QPainter, _c: QColor) -> None:
    # corners
    p.drawLine(QPointF(4, 9), QPointF(4, 4))
    p.drawLine(QPointF(4, 4), QPointF(9, 4))
    p.drawLine(QPointF(15, 4), QPointF(20, 4))
    p.drawLine(QPointF(20, 4), QPointF(20, 9))
    p.drawLine(QPointF(20, 15), QPointF(20, 20))
    p.drawLine(QPointF(20, 20), QPointF(15, 20))
    p.drawLine(QPointF(9, 20), QPointF(4, 20))
    p.drawLine(QPointF(4, 20), QPointF(4, 15))


def _draw_exit(p: QPainter, _c: QColor) -> None:
    p.drawRoundedRect(QRectF(3, 4, 12, 16), 1, 1)
    p.drawLine(QPointF(11, 12), QPointF(21, 12))
    p.drawLine(QPointF(17, 8), QPointF(21, 12))
    p.drawLine(QPointF(17, 16), QPointF(21, 12))


def _draw_about(p: QPainter, _c: QColor) -> None:
    p.drawEllipse(QPointF(12, 12), 8, 8)
    p.drawLine(QPointF(12, 10), QPointF(12, 16))
    p.drawPoint(QPointF(12, 7.5))


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


def toolbar_icon_color(theme_id: str) -> str:
    if theme_id == "clean_light":
        return "#0F172A"
    if theme_id == "cobalt_blue":
        return "#FFFFFF"
    if theme_id == "monokai_pro":
        return "#FCFCFA"
    if theme_id == "darcula":
        return "#A9B7C6"
    return "#E2E8F0"
