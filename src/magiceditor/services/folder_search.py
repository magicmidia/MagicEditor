"""Recursive text search across a directory or in-memory sources (pure I/O)."""

from __future__ import annotations

import os
import re
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path

from magiceditor.core.safe_regex import compile_user_pattern
from magiceditor.core.text_match import PatternError
from magiceditor.services.fs_scope import directory_final, stays_inside

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
    source_key: str | None = None  # e.g. "tab:0" for open-tab hits
    label: str | None = None  # display name override


def search_folder(
    root: Path | str,
    needle: str,
    *,
    case_sensitive: bool = False,
    use_regex: bool = False,
    max_hits: int = 200,
    max_files: int = 2000,
    is_cancelled: Callable[[], bool] | None = None,
    on_progress: Callable[[int, int, int], None] | None = None,
) -> list[SearchHit] | None:
    """Scan text files under ``root`` for ``needle`` (literal or regex).

    Returns ``None`` if ``is_cancelled()`` becomes true mid-scan.
    """
    if not needle:
        return []
    root = Path(root)
    if directory_final(root) is None:
        return []

    try:
        pattern = compile_user_pattern(needle, case_sensitive=case_sensitive, use_regex=use_regex)
    except PatternError:
        return []

    hits: list[SearchHit] = []
    files_seen = 0

    for path in _iter_files(root):
        if is_cancelled is not None and is_cancelled():
            return None
        if files_seen >= max_files or len(hits) >= max_hits:
            break
        files_seen += 1
        if on_progress is not None:
            on_progress(files_seen, max_files, len(hits))
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

        _collect_line_hits(hits, path, text, pattern, max_hits)
        if len(hits) >= max_hits:
            return hits
    return hits


def search_texts(
    sources: Sequence[tuple[str, str, str]],
    needle: str,
    *,
    case_sensitive: bool = False,
    use_regex: bool = False,
    max_hits: int = 200,
) -> list[SearchHit]:
    """Search in-memory sources: each item is ``(source_key, label, content)``."""
    if not needle or not sources:
        return []
    try:
        pattern = compile_user_pattern(needle, case_sensitive=case_sensitive, use_regex=use_regex)
    except PatternError:
        return []

    hits: list[SearchHit] = []
    for key, label, content in sources:
        path = Path(label)
        _collect_line_hits(
            hits,
            path,
            content,
            pattern,
            max_hits,
            source_key=key,
            label=label,
        )
        if len(hits) >= max_hits:
            break
    return hits


def _collect_line_hits(
    hits: list[SearchHit],
    path: Path,
    text: str,
    pattern: re.Pattern[str],
    max_hits: int,
    *,
    source_key: str | None = None,
    label: str | None = None,
) -> None:
    for i, line in enumerate(text.splitlines(), start=1):
        m = pattern.search(line)
        if m is None:
            continue
        hits.append(
            SearchHit(
                path=path,
                line=i,
                column=m.start() + 1,
                text=line.strip()[:200],
                source_key=source_key,
                label=label,
            )
        )
        if len(hits) >= max_hits:
            return


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
    if directory_final(root) is None:
        return
    # Do not descend into directory links. File links are checked below.
    if hasattr(root, "walk"):
        walker = root.walk(follow_symlinks=False)
    else:
        walker = os.walk(root, followlinks=False)
    for dirpath, dirnames, filenames in walker:
        dirnames[:] = [d for d in dirnames if d not in skip_dirs and not d.startswith(".")]
        base = Path(dirpath)
        for name in filenames:
            p = base / name
            if p.suffix.lower() in _SKIP_SUFFIXES:
                continue
            if not stays_inside(p, root):
                continue
            yield p
