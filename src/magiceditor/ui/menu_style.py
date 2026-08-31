"""Fusion menu chrome: compact rows, check mark, right-aligned shortcuts."""

from __future__ import annotations

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QPainter, QPalette, QPen, QPolygonF
from PyQt6.QtWidgets import QProxyStyle, QStyle, QStyleOption, QStyleOptionMenuItem


class MenuChromeStyle(QProxyStyle):
    """Keeps Fusion shortcut column; draws a tick for checked items."""

    _ITEM_H = 22

    def sizeFromContents(self, ct, opt, size, widget=None):  # type: ignore[no-untyped-def]
        sz = super().sizeFromContents(ct, opt, size, widget)
        if ct == QStyle.ContentsType.CT_MenuItem and isinstance(opt, QStyleOptionMenuItem):
            kind = opt.menuItemType
            if kind == QStyleOptionMenuItem.MenuItemType.Normal:
                sz.setHeight(self._ITEM_H)
            elif kind == QStyleOptionMenuItem.MenuItemType.Separator:
                sz.setHeight(max(6, sz.height()))
        return sz

    def pixelMetric(self, metric, option=None, widget=None):  # type: ignore[no-untyped-def]
        if metric == QStyle.PixelMetric.PM_SmallIconSize:
            return 16
        if metric in {
            QStyle.PixelMetric.PM_IndicatorWidth,
            QStyle.PixelMetric.PM_IndicatorHeight,
            QStyle.PixelMetric.PM_ExclusiveIndicatorWidth,
            QStyle.PixelMetric.PM_ExclusiveIndicatorHeight,
        }:
            return 14
        return super().pixelMetric(metric, option, widget)

    def drawPrimitive(self, element, option, painter, widget=None):  # type: ignore[no-untyped-def]
        if element == QStyle.PrimitiveElement.PE_IndicatorMenuCheckMark:
            draw_menu_check(option, painter)
            return
        super().drawPrimitive(element, option, painter, widget)


def draw_menu_check(option: QStyleOption, painter: QPainter) -> None:
    """Tick mark inside *option.rect* (palette-aware)."""
    rect = option.rect
    if rect.width() < 6 or rect.height() < 6:
        return
    selected = bool(option.state & QStyle.StateFlag.State_Selected)
    pal = option.palette
    color = pal.color(
        QPalette.ColorRole.HighlightedText if selected else QPalette.ColorRole.WindowText
    )
    if color.alpha() < 40:
        color = QColor("#FFD700") if selected else QColor("#E5E2E1")
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    pen = QPen(color)
    pen.setWidthF(max(1.6, rect.height() / 8))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
    painter.drawPolyline(
        QPolygonF(
            [
                QPointF(x + w * 0.18, y + h * 0.54),
                QPointF(x + w * 0.40, y + h * 0.76),
                QPointF(x + w * 0.84, y + h * 0.24),
            ]
        )
    )
    painter.restore()


def apply_menu_chrome(app: object) -> None:
    """Wrap the current app style once (call after ``setStyle('Fusion')``)."""
    setter = getattr(app, "setStyle", None)
    getter = getattr(app, "style", None)
    if setter is None or getter is None:
        return
    current = getter()
    if isinstance(current, MenuChromeStyle):
        return
    setter(MenuChromeStyle(current))
