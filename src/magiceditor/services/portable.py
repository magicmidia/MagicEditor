"""Portable mode detection (config beside the executable)."""

from __future__ import annotations

import sys
from pathlib import Path


def executable_dir() -> Path:
    """Directory containing the running executable or project root fallback."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    # Dev: package lives in src/magiceditor — use cwd
    return Path.cwd()


def is_portable_mode(base: Path | None = None) -> bool:
    """True if ``portable.ini`` or ``config/`` beside the app signals portable."""
    root = base if base is not None else executable_dir()
    if (root / "portable.ini").is_file():
        return True
    return (root / "config").is_dir() and (root / "config" / "portable.flag").is_file()


def portable_config_dir(base: Path | None = None) -> Path | None:
    """Return portable config directory when in portable mode, else None."""
    root = base if base is not None else executable_dir()
    if not is_portable_mode(root):
        return None
    cfg = root / "config"
    cfg.mkdir(parents=True, exist_ok=True)
    return cfg
