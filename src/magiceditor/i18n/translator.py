"""JSON-backed translator with live language switch."""

from __future__ import annotations

import json
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

from magiceditor.paths import locales_dir


class TranslatorManager(QObject):
    """Load ``locales/<lang>.json`` and notify listeners on change."""

    language_changed = pyqtSignal(str)

    def __init__(
        self,
        locales_path: Path | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._locales_dir = locales_path or locales_dir()
        self._lang = "pt_BR"
        self._catalog: dict[str, str] = {}

    @property
    def language(self) -> str:
        return self._lang

    def available_languages(self) -> list[str]:
        if not self._locales_dir.is_dir():
            return []
        return sorted(p.stem for p in self._locales_dir.glob("*.json"))

    def load(self, lang: str) -> None:
        path = self._locales_dir / f"{lang}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"Invalid locale file: {path}")
        self._catalog = {str(k): str(v) for k, v in data.items()}
        self._lang = lang
        self.language_changed.emit(lang)

    def t(self, key: str, default: str | None = None) -> str:
        return self._catalog.get(key, default if default is not None else key)
