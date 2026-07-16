"""Qt syntax highlighter driven by pure core rules."""

from __future__ import annotations

from PyQt6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat, QTextDocument

from magiceditor.core.syntax.rules import tokenize_line

# kind -> (fg hex, bold)
_PALETTE: dict[str, tuple[str, bool]] = {
    "keyword": ("#C792EA", True),
    "string": ("#C3E88D", False),
    "comment": ("#546E7A", False),
    "number": ("#F78C6C", False),
    "decorator": ("#82AAFF", False),
    "heading": ("#82AAFF", True),
    "code": ("#89DDFF", False),
    "link": ("#80CBC4", False),
}

# Slightly softer on light themes (applied when canvas is light — caller can override)
_PALETTE_LIGHT: dict[str, tuple[str, bool]] = {
    "keyword": ("#7C3AED", True),
    "string": ("#15803D", False),
    "comment": ("#64748B", False),
    "number": ("#C2410C", False),
    "decorator": ("#2563EB", False),
    "heading": ("#1D4ED8", True),
    "code": ("#0E7490", False),
    "link": ("#0F766E", False),
}


class MagicHighlighter(QSyntaxHighlighter):
    def __init__(self, document: QTextDocument, language: str = "text") -> None:
        super().__init__(document)
        self._language = language
        self._light = False
        self._formats: dict[str, QTextCharFormat] = {}
        self._rebuild_formats()

    @property
    def language(self) -> str:
        return self._language

    def set_language(self, language: str) -> None:
        if language == self._language:
            return
        self._language = language
        self.rehighlight()

    def set_light_theme(self, light: bool) -> None:
        if light == self._light:
            return
        self._light = light
        self._rebuild_formats()
        self.rehighlight()

    def _rebuild_formats(self) -> None:
        palette = _PALETTE_LIGHT if self._light else _PALETTE
        self._formats = {}
        for kind, (color, bold) in palette.items():
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            if bold:
                fmt.setFontWeight(QFont.Weight.Bold)
            self._formats[kind] = fmt

    def highlightBlock(self, text: str) -> None:
        """Qt override — highlight a single block."""
        if self._language in {"", "text"} or not text:
            return
        # Skip huge lines to keep typing snappy
        if len(text) > 8000:
            return
        for start, length, kind in tokenize_line(text, self._language):
            fmt = self._formats.get(kind)
            if fmt is not None:
                self.setFormat(start, length, fmt)
