"""QSS theme manager (five native themes planned)."""

from __future__ import annotations

from pathlib import Path

NATIVE_THEMES = (
    "clean_light",
    "midnight_dark",
    "darcula",
    "cobalt_blue",
    "monokai_pro",
)


class ThemeManager:
    def __init__(self, themes_dir: Path | None = None) -> None:
        self._themes_dir = themes_dir
        self._current = "midnight_dark"

    @property
    def current(self) -> str:
        return self._current

    def list_themes(self) -> tuple[str, ...]:
        return NATIVE_THEMES
