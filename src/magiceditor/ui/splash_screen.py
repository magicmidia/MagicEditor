"""Modern gradient splash screen for MagicEditor startup."""

from __future__ import annotations

import time
from typing import Any

from PyQt6.QtCore import QPointF, QRect, QRectF, Qt, QTimer
from PyQt6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PyQt6.QtWidgets import QApplication, QWidget

from magiceditor.ui.app_icon import load_app_icon
from magiceditor.version import APP_NAME, SPLASH_MIN_SECONDS, version_display


class MagicSplash(QWidget):
    """Frameless splash with deep gradient, monogram, title and version."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setFixedSize(520, 320)
        self.setWindowTitle(APP_NAME)
        self._message = "Carregando…"
        self._progress = 0.0  # 0..1 soft pulse
        self._t0 = time.monotonic()
        self._pulse = QTimer(self)
        self._pulse.timeout.connect(self._tick)
        self._pulse.start(32)
        self._center_on_screen()

    def _center_on_screen(self) -> None:
        app = QApplication.instance()
        if app is None:
            return
        screen = app.primaryScreen()  # type: ignore[union-attr]
        if screen is None:
            return
        geo = screen.availableGeometry()
        self.move(
            geo.center().x() - self.width() // 2,
            geo.center().y() - self.height() // 2,
        )

    def set_message(self, text: str) -> None:
        self._message = text
        self.update()

    def _tick(self) -> None:
        # Soft progress towards 1 over min splash duration
        elapsed = time.monotonic() - self._t0
        self._progress = min(1.0, elapsed / max(0.1, SPLASH_MIN_SECONDS))
        self.update()

    def paintEvent(self, _event: Any) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()
        radius = 18.0

        # Outer soft shadow plate
        shadow = QColor(0, 0, 0, 90)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(shadow)
        painter.drawRoundedRect(QRectF(6, 8, w - 12, h - 10), radius, radius)

        # Main card path
        card = QRectF(0, 0, w - 4, h - 6)
        path = QPainterPath()
        path.addRoundedRect(card, radius, radius)

        # Multi-stop diagonal gradient (Luminous Void inspired)
        grad = QLinearGradient(QPointF(0, 0), QPointF(w, h))
        grad.setColorAt(0.0, QColor("#0B0A0F"))
        grad.setColorAt(0.35, QColor("#1A1428"))
        grad.setColorAt(0.65, QColor("#1C1B1B"))
        grad.setColorAt(1.0, QColor("#0E0E0E"))
        painter.fillPath(path, grad)

        # Gold radial glow top-right
        glow = QRadialGradient(QPointF(w * 0.78, h * 0.22), w * 0.55)
        glow.setColorAt(0.0, QColor(255, 215, 0, 55))
        glow.setColorAt(0.45, QColor(255, 180, 40, 18))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillPath(path, glow)

        # Violet wash bottom-left
        wash = QRadialGradient(QPointF(w * 0.18, h * 0.85), w * 0.5)
        wash.setColorAt(0.0, QColor(120, 80, 220, 40))
        wash.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillPath(path, wash)

        # Thin gold border
        pen = QPen(QColor(255, 215, 0, 70))
        pen.setWidthF(1.2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(card.adjusted(0.5, 0.5, -0.5, -0.5), radius, radius)

        # Monogram tile
        tile = 72
        tx = int((w - tile) / 2)
        ty = 48
        self._paint_monogram(painter, QRect(tx, ty, tile, tile))

        # Title
        painter.setPen(QColor("#FFF6DF"))
        title_font = QFont("Segoe UI", 22)
        title_font.setWeight(QFont.Weight.DemiBold)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.2)
        painter.setFont(title_font)
        painter.drawText(
            QRect(0, ty + tile + 16, w, 36),
            int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter),
            APP_NAME,
        )

        # Version badge
        ver = version_display()
        badge_font = QFont("Segoe UI", 10)
        badge_font.setWeight(QFont.Weight.Medium)
        painter.setFont(badge_font)
        fm = painter.fontMetrics()
        bw = fm.horizontalAdvance(ver) + 24
        bh = 22
        bx = int((w - bw) / 2)
        by = ty + tile + 56
        badge_rect = QRectF(bx, by, bw, bh)
        painter.setPen(QPen(QColor(255, 215, 0, 120)))
        painter.setBrush(QColor(255, 215, 0, 28))
        painter.drawRoundedRect(badge_rect, 11, 11)
        painter.setPen(QColor("#FFD700"))
        painter.drawText(
            badge_rect.toRect(),
            int(Qt.AlignmentFlag.AlignCenter),
            ver,
        )

        # Tagline
        painter.setPen(QColor("#999077"))
        tag_font = QFont("Segoe UI", 9)
        painter.setFont(tag_font)
        painter.drawText(
            QRect(40, by + 28, w - 80, 20),
            int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter),
            "Editor de texto e código · alto desempenho",
        )

        # Progress bar
        bar_w = w - 100
        bar_h = 3
        bar_x = 50
        bar_y = h - 48
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 18))
        painter.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), 2, 2)
        fill_w = max(8.0, bar_w * self._progress)
        bar_grad = QLinearGradient(QPointF(bar_x, 0), QPointF(bar_x + fill_w, 0))
        bar_grad.setColorAt(0.0, QColor("#A78BFA"))
        bar_grad.setColorAt(1.0, QColor("#FFD700"))
        painter.setBrush(bar_grad)
        painter.drawRoundedRect(QRectF(bar_x, bar_y, fill_w, bar_h), 2, 2)

        # Status message
        painter.setPen(QColor("#B7B5B4"))
        msg_font = QFont("Segoe UI", 8)
        painter.setFont(msg_font)
        painter.drawText(
            QRect(40, bar_y + 10, w - 80, 18),
            int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter),
            self._message,
        )
        painter.end()

    def _paint_monogram(self, painter: QPainter, rect: QRect) -> None:
        painter.save()
        # Try app icon
        try:
            ico = load_app_icon()
            if not ico.isNull():
                pm = ico.pixmap(rect.width(), rect.height())
                painter.drawPixmap(rect, pm)
                painter.restore()
                return
        except Exception:
            pass
        # Fallback painted M
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#1C1B1B"))
        painter.drawRoundedRect(QRectF(rect), rect.width() * 0.22, rect.height() * 0.22)
        pen = QPen(QColor("#FFD700"))
        pen.setWidthF(max(2.5, rect.width() * 0.07))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        m = rect.width() * 0.22
        x0, y0 = rect.x(), rect.y()
        s = rect.width()
        painter.drawLine(int(x0 + m), int(y0 + s - m), int(x0 + m), int(y0 + m * 1.1))
        painter.drawLine(int(x0 + m), int(y0 + m * 1.1), int(x0 + s / 2), int(y0 + s * 0.55))
        painter.drawLine(int(x0 + s / 2), int(y0 + s * 0.55), int(x0 + s - m), int(y0 + m * 1.1))
        painter.drawLine(int(x0 + s - m), int(y0 + m * 1.1), int(x0 + s - m), int(y0 + s - m))
        painter.restore()

    def finish_after_minimum(self, app: QApplication) -> None:
        """Block until SPLASH_MIN_SECONDS elapsed, pumping the event loop."""
        deadline = self._t0 + SPLASH_MIN_SECONDS
        while time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.016)
        self._pulse.stop()
        self.close()
