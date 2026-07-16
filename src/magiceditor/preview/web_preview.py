"""Lightweight HTML/Markdown preview (QTextBrowser — portable & fast)."""

from __future__ import annotations

from PyQt6.QtWidgets import QTextBrowser, QVBoxLayout, QWidget

from magiceditor.preview.markdown_preview import render_markdown


class WebPreview(QWidget):
    """Renders HTML/Markdown without WebEngine (smaller, faster shipping)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._view = QTextBrowser(self)
        self._view.setOpenExternalLinks(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._view)

    def set_html(self, html: str) -> None:
        self._view.setHtml(html)

    def set_markdown(self, source: str) -> None:
        body = render_markdown(source)
        self.set_html(
            "<html><head><style>"
            "body{font-family:Segoe UI,sans-serif;padding:16px;line-height:1.5;}"
            "pre,code{font-family:Consolas,monospace;background:rgba(127,127,127,.12);"
            "border-radius:6px;}"
            "pre{padding:12px;overflow:auto;}"
            "code{padding:1px 4px;}"
            "h1,h2,h3{margin-top:1.2em;}"
            "</style></head><body>"
            f"{body}</body></html>"
        )
