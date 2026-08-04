"""Premium About dialog — card layout, monogram, version."""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


def _monogram_pixmap(size: int = 64, accent: str = "#FFD700", bg: str = "#1C1B1B") -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setBrush(QColor(bg))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(0, 0, size, size, size * 0.22, size * 0.22)
    pen = QPen(QColor(accent))
    pen.setWidthF(max(2.0, size * 0.06))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Stylized "M"
    m = size * 0.22
    p.drawLine(int(m), int(size - m), int(m), int(m * 1.1))
    p.drawLine(int(m), int(m * 1.1), int(size / 2), int(size * 0.55))
    p.drawLine(int(size / 2), int(size * 0.55), int(size - m), int(m * 1.1))
    p.drawLine(int(size - m), int(m * 1.1), int(size - m), int(size - m))
    p.end()
    return pm


class AboutDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        tr: Any | None = None,
        theme_id: str = "luminous_void",
    ) -> None:
        super().__init__(parent)
        self.setObjectName("aboutDialog")
        self.setModal(True)
        self.setMinimumWidth(400)

        def t(key: str, default: str) -> str:
            return tr.t(key, default) if tr is not None else default

        self.setWindowTitle(t("msg.about_title", "Sobre o MagicEditor"))

        accent = {
            "luminous_void": "#FFD700",
            "clean_light": "#2563EB",
            "midnight_dark": "#22D3EE",
            "darcula": "#6897BB",
            "cobalt_blue": "#FFCC00",
            "monokai_pro": "#A9DC76",
        }.get(theme_id, "#FFD700")
        bg = "#2A2929" if theme_id != "clean_light" else "#F1F5F9"

        logo = QLabel(self)
        try:
            from magiceditor.ui.app_icon import load_app_icon

            app_ico = load_app_icon()
            if not app_ico.isNull():
                logo.setPixmap(app_ico.pixmap(72, 72))
            else:
                logo.setPixmap(_monogram_pixmap(72, accent, bg))
        except Exception:
            logo.setPixmap(_monogram_pixmap(72, accent, bg))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("MagicEditor", self)
        tf = QFont(title.font())
        tf.setPointSize(16)
        tf.setBold(True)
        title.setFont(tf)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("aboutTitle")

        from magiceditor.version import about_version_text

        version = QLabel(
            about_version_text(prefix=t("about.version_prefix", "Versão")),
            self,
        )
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setObjectName("aboutMuted")

        body = QLabel(
            t(
                "msg.about_body",
                "<p>Editor de texto e código moderno e rápido para o dia a dia.</p>"
                "<p>Piece table · mmap · pré-visualização · temas · i18n</p>",
            ),
            self,
        )
        body.setWordWrap(True)
        body.setTextFormat(Qt.TextFormat.RichText)
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.setObjectName("aboutBody")
        body.setOpenExternalLinks(True)

        tagline = QLabel(
            t(
                "about.tagline",
                "Zero travamentos em arquivos gigantes. Design Luminous Void.",
            ),
            self,
        )
        tagline.setWordWrap(True)
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline.setObjectName("aboutMuted")

        btn = QPushButton(t("dialog.ok", "OK"), self)
        btn.setObjectName("aboutOk")
        btn.setDefault(True)
        btn.setMinimumWidth(100)
        btn.clicked.connect(self.accept)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_row.addWidget(btn)
        btn_row.addStretch(1)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 24)
        root.setSpacing(12)
        root.addWidget(logo)
        root.addWidget(title)
        root.addWidget(version)
        root.addSpacing(4)
        root.addWidget(body)
        root.addWidget(tagline)
        root.addSpacing(12)
        root.addLayout(btn_row)
