"""Viewport syntax token cache (K2) — one tokenize per dirty line."""

from __future__ import annotations

from magiceditor.core.syntax.rules import tokenize_line

TokenSpan = tuple[int, int, str]


class LineTokenCache:
    def __init__(self) -> None:
        self._rev = 0
        self._hits: dict[tuple[int, int, str], list[TokenSpan]] = {}

    def invalidate(self) -> None:
        self._rev += 1
        self._hits.clear()

    def tokens(self, line: int, text: str, lang: str) -> list[TokenSpan]:
        key = (line, self._rev, lang, hash(text))
        cached = self._hits.get(key)
        if cached is not None:
            return cached
        spans = tokenize_line(text, lang)
        self._hits[key] = spans
        if len(self._hits) > 400:
            self._hits.clear()
            self._hits[key] = spans
        return spans
