"""Resolve package resource paths (source tree and frozen exe)."""

from __future__ import annotations

import os
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


def changelog_path() -> Path:
    """Bundled ``docs/CHANGELOG.md`` (dev tree or frozen ``_MEIPASS``)."""
    bundled = resource_root() / "docs" / "CHANGELOG.md"
    if bundled.is_file():
        return bundled
    return repo_root() / "docs" / "CHANGELOG.md"


def read_changelog() -> str:
    """Changelog text, or an empty string when the file is missing."""
    path = changelog_path()
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


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


def user_data_dir(*, local_app_data: str | Path | None = None) -> Path:
    """Per-user writable dir (``%LOCALAPPDATA%\\MagicEditor`` on Windows)."""
    raw = local_app_data
    if raw is None:
        raw = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    if raw:
        return Path(raw) / "MagicEditor"
    return Path.home() / ".magiceditor"


def _looks_portable(exe_dir: Path) -> bool:
    return (exe_dir / "portable.ini").is_file() or (exe_dir / "config" / "portable.flag").is_file()


def _dir_writable(directory: Path) -> bool:
    probe = directory / ".me-write-probe"
    try:
        directory.mkdir(parents=True, exist_ok=True)
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def log_file_path(
    *,
    frozen: bool | None = None,
    exe_dir: Path | None = None,
    local_app_data: str | Path | None = None,
) -> Path:
    """Dev: repo root. Installed EXE: ``%LOCALAPPDATA%\\MagicEditor``.

    Portable (``portable.ini`` beside the EXE) stays next to the EXE when that
    folder is writable; otherwise it falls back to the user data dir.
    """
    name = "MagicEditor.log"
    use_frozen = is_frozen() if frozen is None else frozen
    if not use_frozen:
        return repo_root() / name
    parent = exe_dir if exe_dir is not None else Path(sys.executable).resolve().parent
    if _looks_portable(parent) and _dir_writable(parent):
        return parent / name
    return user_data_dir(local_app_data=local_app_data) / name
