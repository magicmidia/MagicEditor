"""Resolve package resource paths (source tree and frozen exe)."""

from __future__ import annotations

import sys
from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PACKAGE_DIR.parents[1]


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def resource_root() -> Path:
    """Root for bundled read-only assets (locales, themes)."""
    if is_frozen():
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent
    if (_REPO_ROOT / "pyproject.toml").is_file():
        return _REPO_ROOT
    return _PACKAGE_DIR.parent


def repo_root() -> Path:
    """Project root in dev; directory of the executable when frozen."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    if (_REPO_ROOT / "pyproject.toml").is_file():
        return _REPO_ROOT
    return _PACKAGE_DIR.parent


def locales_dir() -> Path:
    return resource_root() / "locales"


def themes_dir() -> Path:
    return resource_root() / "resources" / "themes"


def fonts_dir() -> Path:
    return resource_root() / "resources" / "fonts"


def icons_dir() -> Path:
    return resource_root() / "resources" / "icons"


def app_icon_path() -> Path:
    """Windows multi-size application icon (``.ico``)."""
    return icons_dir() / "app" / "magiceditor.ico"
