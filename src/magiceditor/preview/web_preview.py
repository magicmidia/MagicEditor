"""Lightweight HTML/Markdown preview (QTextBrowser — portable & fast)."""

from __future__ import annotations

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QTextBrowser, QVBoxLayout, QWidget

from magiceditor.preview.markdown_preview import render_markdown
from magiceditor.preview.preview_css import preview_css
from magiceditor.preview.sanitize import sanitize_html
from magiceditor.themes.tokens import chrome_tokens


class _OfflineBrowser(QTextBrowser):
    """Preview HTML is untrusted. Do not fetch http, file, or data resources."""

    def loadResource(self, resource_type: int, name: object) -> None:
        del resource_type, name


class WebPreview(QWidget):
    """Renders HTML/Markdown without WebEngine (smaller, faster shipping)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._theme_id = "luminous_void"
        self._fragment = ""
        self._view = _OfflineBrowser(self)
        self._view.setObjectName("markdownPreview")
        self._view.setOpenExternalLinks(False)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._view)
        self.apply_theme(self._theme_id)

    def apply_theme(self, theme_id: str) -> None:
        self._theme_id = theme_id or "luminous_void"
        tok = chrome_tokens(self._theme_id)
        pal = self._view.palette()
        pal.setColor(QPalette.ColorRole.Base, QColor(tok.bg))
        pal.setColor(QPalette.ColorRole.Text, QColor(tok.fg))
        pal.setColor(QPalette.ColorRole.Window, QColor(tok.bg))
        pal.setColor(QPalette.ColorRole.WindowText, QColor(tok.fg))
        self._view.setPalette(pal)
        self._view.document().setDefaultStyleSheet(preview_css(self._theme_id))
        if self._fragment:
            self._view.setHtml(self._fragment)

    def set_html(self, html: str) -> None:
        self._fragment = sanitize_html(html)
        self._view.document().setDefaultStyleSheet(preview_css(self._theme_id))
        self._view.setHtml(self._fragment)

    def set_markdown(self, source: str) -> None:
        self.set_html(render_markdown(source))
