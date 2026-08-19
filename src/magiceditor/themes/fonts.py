"""Theme-layer font family (no ui/ import)."""

from __future__ import annotations

FAMILY = "Cascadia Code"


def qss_font_family() -> str:
    """Quoted family name safe for QSS font-family rules."""
    return f'"{FAMILY}", "Cascadia Code", "Consolas", monospace'
