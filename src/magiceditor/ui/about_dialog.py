"""Premium About dialog — card layout, monogram, version."""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPalette, QPen, QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from magiceditor.themes.tokens import chrome_tokens


def _monogram_pixmap(size: int = 64, accent: str = "#FFD700", bg: str = "#141722") -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setBrush(QColor(bg))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(0, 0, size, size, size * 0.22, size * 0.22)
    pen = QPen(QColor(accent))
    pen.setWidthF(max(2.0, size * 0.08))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    m_x = size * 0.18
    m_top = size * 0.24
    m_bot = size * 0.76
    m_mid = size * 0.54
    cx = size / 2.0
    p.drawLine(int(m_x), int(m_bot), int(m_x), int(m_top))
    p.drawLine(int(m_x), int(m_top), int(cx), int(m_mid))
    p.drawLine(int(cx), int(m_mid), int(size - m_x), int(m_top))
    p.drawLine(int(size - m_x), int(m_top), int(size - m_x), int(m_bot))
    caret_pen = QPen(QColor("#FFF8E1"))
    caret_pen.setWidthF(max(1.5, size * 0.06))
    caret_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(caret_pen)
    p.drawLine(int(cx), int(m_mid), int(cx), int(m_bot))
    p.end()
    return pm


def _paint_label(label: QLabel, color: str) -> None:
    """Force readable text: QSS is ignored on RichText QLabel."""
    pal = label.palette()
    qcolor = QColor(color)
    pal.setColor(QPalette.ColorRole.WindowText, qcolor)
    pal.setColor(QPalette.ColorRole.Text, qcolor)
    label.setPalette(pal)
    label.setForegroundRole(QPalette.ColorRole.WindowText)
    label.setAutoFillBackground(False)


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
        self.setMinimumWidth(480)

        def t(key: str, default: str) -> str:
            return tr.t(key, default) if tr is not None else default

        self.setWindowTitle(t("msg.about_title", "Sobre o MagicEditor"))

        tok = chrome_tokens(theme_id)
        accent = tok.accent
        bg = tok.code_bg
        self.setStyleSheet(
            f"QDialog#aboutDialog {{ background-color: {tok.surface}; color: {tok.fg}; }}"
            f"QDialog#aboutDialog QLabel {{ color: {tok.fg}; background: transparent; }}"
            f"QLabel#aboutTitle {{ color: {tok.heading}; }}"
            f"QLabel#aboutMuted {{ color: {tok.muted}; }}"
            f"QLabel#aboutBody {{ color: {tok.fg}; }}"
            f"QPushButton#aboutOk {{ color: {tok.heading}; }}"
        )

        logo = QLabel(self)
        try:
            from magiceditor.ui.app_icon import load_app_icon

            app_ico = load_app_icon()
            if not app_ico.isNull():
                logo.setPixmap(app_ico.pixmap(88, 88))
            else:
                logo.setPixmap(_monogram_pixmap(88, accent, bg))
        except Exception:
            logo.setPixmap(_monogram_pixmap(88, accent, bg))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("MagicEditor", self)
        tf = QFont(title.font())
        tf.setPointSize(16)
        tf.setBold(True)
        title.setFont(tf)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("aboutTitle")
        _paint_label(title, tok.heading)

        from magiceditor.version import about_version_text

        version = QLabel(
            about_version_text(prefix=t("about.version_prefix", "Versão")),
            self,
        )
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setObjectName("aboutMuted")
        _paint_label(version, tok.muted)

        body = QLabel(
            t(
                "msg.about_body",
                "<p>Editor de texto e código para o dia a dia, feito para arquivos grandes.</p>"
                "<ul><li>Recuperação do texto não salvo se faltar energia</li>"
                "<li>Pré-visualização de Markdown, com impressão dessa visualização</li>"
                "<li>Hashes do arquivo ativo: MD5, SHA-256, SHA-512 e outros</li>"
                "<li>Piece table e mmap: o arquivo inteiro não entra na memória</li></ul>",
            ),
            self,
        )
        body.setWordWrap(True)
        body.setTextFormat(Qt.TextFormat.RichText)
        body.setAlignment(Qt.AlignmentFlag.AlignLeft)
        body.setObjectName("aboutBody")
        body.setOpenExternalLinks(True)
        # Qt rich-text ignores QSS color — wrap HTML so dark themes stay readable.
        raw = body.text()
        body.setText(f'<div style="color:{tok.fg};">{raw}</div>')
        _paint_label(body, tok.fg)

        tagline = QLabel(
            t(
                "about.tagline",
                "Arquivos grandes sem carregar o arquivo inteiro na memória.",
            ),
            self,
        )
        tagline.setWordWrap(True)
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline.setObjectName("aboutMuted")
        _paint_label(tagline, tok.muted)

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
