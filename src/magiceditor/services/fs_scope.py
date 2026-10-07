"""Keep a folder walk inside the directory the user opened.

Classification uses ``os.lstat`` and ``os.readlink`` only. ``Path.resolve``
opens the target (``CreateFile`` on Windows) and can block on a pipe.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

_MAX_LINKS = 8


def regular_file(path: Path | str) -> str | None:
    """Absolute path of an existing regular file, or None.

    Symlinks are followed, up to a short chain. A directory, pipe, device,
    or broken link is not a regular file.
    """
    return _follow(path, want_dir=False)


def directory_final(path: Path | str) -> str | None:
    """Absolute path of an existing directory, following links."""
    return _follow(path, want_dir=True)


def stays_inside(path: Path, root: Path) -> bool:
    """True when ``path`` is a regular file whose real location is under ``root``.

    A name inside the folder that points at a file outside it is not inside,
    so search and quick-open skip it. Hard-link names that already live in
    the folder stay eligible: resolving them would walk the volume.
    """
    final = regular_file(path)
    base = directory_final(root)
    if final is None or base is None:
        return False
    return _is_under(final, base)


def _follow(path: Path | str, *, want_dir: bool) -> str | None:
    current = os.path.abspath(os.fspath(path))
    seen: set[str] = set()
    for _ in range(_MAX_LINKS + 1):
        key = os.path.normcase(current)
        if key in seen:
            return None
        seen.add(key)
        try:
            mode = os.lstat(current).st_mode
        except OSError:
            return None
        if stat.S_ISLNK(mode):
            try:
                target = os.readlink(current)
            except OSError:
                return None
            current = _join_link(current, target)
            continue
        if want_dir and stat.S_ISDIR(mode):
            return current
        if not want_dir and stat.S_ISREG(mode):
            return current
        return None
    return None


def _join_link(link: str, target: str) -> str:
    if target.startswith("\\\\?\\UNC\\"):
        target = "\\\\" + target[8:]
    elif target.startswith("\\\\?\\"):
        target = target[4:]
    if not os.path.isabs(target):
        target = os.path.join(os.path.dirname(link), target)
    return os.path.abspath(target)


def _is_under(child: str, parent: str) -> bool:
    child_n = os.path.normcase(child)
    parent_n = os.path.normcase(parent)
    if child_n == parent_n:
        return False
    try:
        return os.path.commonpath((child_n, parent_n)) == parent_n
    except ValueError:
        return False
