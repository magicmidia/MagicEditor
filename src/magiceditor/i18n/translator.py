"""JSON-backed translator with live language switch (Qt signals later)."""

from __future__ import annotations

import json
from pathlib import Path


class TranslatorManager:
    """Load ``locales/<lang>.json`` and resolve keys.

    Wire ``language_changed`` pyqtSignal when integrating with widgets.
    """

    def __init__(self, locales_dir: Path | None = None) -> None:
        self._locales_dir = locales_dir
        self._lang = "en_US"
        self._catalog: dict[str, str] = {}

    @property
    def language(self) -> str:
        return self._lang

    def load(self, lang: str) -> None:
        if self._locales_dir is None:
            self._lang = lang
            self._catalog = {}
            return
        path = self._locales_dir / f"{lang}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"Invalid locale file: {path}")
        self._catalog = {str(k): str(v) for k, v in data.items()}
        self._lang = lang

    def t(self, key: str, default: str | None = None) -> str:
        return self._catalog.get(key, default if default is not None else key)
