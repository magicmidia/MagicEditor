"""Crash-recovery sidecar. Qt-free; the file is the source of truth for unsaved text.

QSettings (the registry on Windows) is a poor store for large drafts. Preferences stay
in QSettings. This JSON file is written atomically and wins over registry drafts on load,
including an empty list so a closed session is not resurrected from a stale registry.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from magiceditor.services.atomic_io import write_bytes_atomic
from magiceditor.services.session_state import SessionState, normalize_path

RECOVERY_VERSION = 1
MAX_DRAFTS = 24
MAX_DRAFT_CHARS = 400_000


def normalize_drafts(
    items: object,
    *,
    limit: int = MAX_DRAFTS,
    max_chars: int = MAX_DRAFT_CHARS,
) -> list[dict[str, Any]]:
    """Shared draft serializer for QSettings and the recovery file."""
    if not isinstance(items, list):
        return []
    out: list[dict[str, Any]] = []
    for item in items[: max(0, limit)]:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "")
        if len(text) > max_chars:
            text = text[:max_chars]
        entry: dict[str, Any] = {
            "title": str(item.get("title") or "Untitled")[:120],
            "text": text,
        }
        if item.get("active"):
            entry["active"] = True
        raw_path = item.get("path")
        if isinstance(raw_path, str) and raw_path.strip():
            entry["path"] = raw_path
        marks = item.get("bookmarks")
        if isinstance(marks, list):
            cleaned: list[int] = []
            for x in marks:
                if isinstance(x, bool):
                    continue
                try:
                    cleaned.append(int(x))
                except (TypeError, ValueError):
                    continue
            entry["bookmarks"] = cleaned[:500]
        cur = item.get("cursor")
        if isinstance(cur, (list, tuple)) and len(cur) >= 2:
            try:
                entry["cursor"] = [max(1, int(cur[0])), max(1, int(cur[1]))]
            except (TypeError, ValueError):
                pass
        out.append(entry)
    return out


def _clean_bookmarks(raw: object) -> dict[str, list[int]]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, list[int]] = {}
    for key, lines in raw.items():
        if not isinstance(lines, list):
            continue
        cleaned: list[int] = []
        for x in lines:
            try:
                n = int(x)
            except (TypeError, ValueError):
                continue
            if n >= 0:
                cleaned.append(n)
        cleaned = sorted(set(cleaned))
        if not cleaned:
            continue
        nkey = normalize_path(key) if Path(str(key)).exists() else str(key)
        out[nkey] = cleaned
    return out


def _clean_cursors(raw: object) -> dict[str, tuple[int, int]]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, tuple[int, int]] = {}
    for key, pos in raw.items():
        if not isinstance(pos, (list, tuple)) or len(pos) < 2:
            continue
        try:
            line, col = int(pos[0]), int(pos[1])
        except (TypeError, ValueError):
            continue
        nkey = normalize_path(key) if Path(str(key)).exists() else str(key)
        out[nkey] = (max(line, 1), max(col, 1))
    return out


def _existing_files(raw_files: object) -> list[str]:
    if not isinstance(raw_files, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for raw in raw_files:
        path = Path(str(raw))
        if not path.is_file():
            continue
        key = normalize_path(path)
        if key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def _active_among(raw_active: object, open_files: list[str]) -> str | None:
    if not raw_active or not open_files:
        return open_files[0] if open_files else None
    text = str(raw_active)
    candidate = normalize_path(text) if Path(text).is_file() else text
    if candidate in open_files:
        return candidate
    name = Path(text).name
    for f in open_files:
        if f == candidate or Path(f).name == name:
            return f
    return open_files[0]


def session_recovery_payload(state: SessionState) -> dict[str, Any]:
    """Version-1 snapshot. Open files are limited to paths that still exist."""
    open_files = _existing_files(state.open_files)
    return {
        "version": RECOVERY_VERSION,
        "open_files": open_files,
        "active_file": _active_among(state.active_file, open_files),
        "drafts": normalize_drafts(state.drafts),
        "bookmarks": _clean_bookmarks(state.bookmarks),
        "cursors": {k: [line, col] for k, (line, col) in _clean_cursors(state.cursors).items()},
    }


def write_recovery(path: Path, payload: dict[str, Any]) -> None:
    """Atomic replace. The temp name comes from ``mkstemp``, not a fixed ``.tmp``.

    A predictable ``recovery.json.tmp`` can be planted as a link; opening it
    for write would follow that link. ``mkstemp`` creates a new file instead.
    """
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    write_bytes_atomic(path, data)


def read_recovery(path: Path) -> dict[str, Any] | None:
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError, UnicodeError):
        return None
    if not isinstance(data, dict) or data.get("version") != RECOVERY_VERSION:
        return None
    return data


def apply_recovery(state: SessionState, payload: dict[str, Any]) -> SessionState:
    """Replace session lists even when empty (a closed session must not come back)."""
    if payload.get("version") != RECOVERY_VERSION:
        return state
    open_files = _existing_files(payload.get("open_files"))
    cursors_raw = payload.get("cursors")
    return replace(
        state,
        open_files=open_files,
        active_file=_active_among(payload.get("active_file"), open_files),
        drafts=normalize_drafts(payload.get("drafts")),
        bookmarks=_clean_bookmarks(payload.get("bookmarks")),
        cursors=_clean_cursors(cursors_raw if isinstance(cursors_raw, dict) else {}),
    )
