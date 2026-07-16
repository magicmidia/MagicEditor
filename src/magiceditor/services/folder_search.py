"""Recursive text search across a directory (pure I/O, no Qt)."""

from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

# Skip obvious binaries / huge blobs
_SKIP_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".zip",
    ".7z",
    ".rar",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".pyc",
    ".pyo",
    ".class",
    ".o",
    ".a",
    ".woff",
    ".woff2",
    ".ttf",
    ".otf",
    ".mp3",
    ".mp4",
    ".wav",
    ".gz",
    ".bz2",
}
_MAX_FILE_BYTES = 8 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class SearchHit:
    path: Path
    line: int  # 1-based
    column: int  # 1-based
    text: str  # line content (trimmed)


def search_folder(
    root: Path | str,
    needle: str,
    *,
    case_sensitive: bool = False,
    max_hits: int = 200,
    max_files: int = 2000,
) -> list[SearchHit]:
    """Scan text files under ``root`` for ``needle`` (literal substring)."""
    if not needle:
        return []
    root = Path(root)
    if not root.is_dir():
        return []

    hits: list[SearchHit] = []
    files_seen = 0
    needle_cmp = needle if case_sensitive else needle.lower()

    for path in _iter_files(root):
        if files_seen >= max_files or len(hits) >= max_hits:
            break
        files_seen += 1
        try:
            if path.stat().st_size > _MAX_FILE_BYTES:
                continue
            raw = path.read_bytes()
        except OSError:
            continue
        if b"\x00" in raw[:8192]:
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = raw.decode("latin-1")
            except UnicodeDecodeError:
                continue

        for i, line in enumerate(text.splitlines(), start=1):
            hay = line if case_sensitive else line.lower()
            col = hay.find(needle_cmp)
            if col < 0:
                continue
            hits.append(
                SearchHit(
                    path=path,
                    line=i,
                    column=col + 1,
                    text=line.strip()[:200],
                )
            )
            if len(hits) >= max_hits:
                return hits
    return hits


def _iter_files(root: Path) -> Iterator[Path]:
    skip_dirs = {
        ".git",
        ".hg",
        ".svn",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        "dist",
        "build",
    }
    walker = root.walk() if hasattr(root, "walk") else os.walk(root)
    for dirpath, dirnames, filenames in walker:
        dirnames[:] = [d for d in dirnames if d not in skip_dirs and not d.startswith(".")]
        base = Path(dirpath)
        for name in filenames:
            p = base / name
            if p.suffix.lower() in _SKIP_SUFFIXES:
                continue
            yield p
