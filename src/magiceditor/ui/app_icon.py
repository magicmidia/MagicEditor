"""Application window / taskbar icon (bundled .ico)."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QIcon

from magiceditor.paths import app_icon_path


def load_app_icon(path: Path | None = None) -> QIcon:
    """Load the MagicEditor application icon, or an empty icon if missing."""
    ico_path = path if path is not None else app_icon_path()
    if ico_path.is_file():
        return QIcon(str(ico_path))
    return QIcon()
