"""Menu chrome: compact rows + check primitive."""

from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")
pytest.importorskip("pytestqt")

from PyQt6.QtCore import QRect, QSize
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPalette, QPixmap
from PyQt6.QtWidgets import QStyle, QStyleOption, QStyleOptionMenuItem

from magiceditor.ui.menu_style import MenuChromeStyle, apply_menu_chrome, draw_menu_check


def test_menu_item_height_is_compact(qapp) -> None:
    # A leftover application stylesheet (e.g. from a MainWindow test) makes
    # Qt ignore setStyle() — clear it so the proxy wrap takes effect.
    qapp.setStyleSheet("")
    apply_menu_chrome(qapp)
    style = qapp.style()
    assert isinstance(style, MenuChromeStyle)
    opt = QStyleOptionMenuItem()
    opt.menuItemType = QStyleOptionMenuItem.MenuItemType.Normal
    opt.fontMetrics = QFontMetrics(QFont())
    sz = style.sizeFromContents(QStyle.ContentsType.CT_MenuItem, opt, QSize(120, 40), None)
    assert sz.height() == 22


def test_draw_menu_check_paints(qapp) -> None:
    pm = QPixmap(16, 16)
    pm.fill(QColor("#201F1F"))
    painter = QPainter(pm)
    opt = QStyleOption()
    opt.rect = QRect(0, 0, 16, 16)
    opt.palette = QPalette(QColor("#E5E2E1"))
    opt.state = QStyle.StateFlag.State_On
    draw_menu_check(opt, painter)
    painter.end()
    img = pm.toImage()
    colors = {img.pixelColor(x, y).name() for x in range(16) for y in range(16)}
    assert len(colors) > 1
