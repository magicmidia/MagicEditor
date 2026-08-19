"""Session restore / collect helpers (J1.2) — no widget I/O policy."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from magiceditor.services.session_state import SessionState, normalize_path

RESTORE_FILE_CAP = 16
DRAFT_TEXT_CAP = 400_000


@dataclass(frozen=True)
class TabSessionView:
    """One open tab as the session collector sees it (no Qt)."""

    path: Path | None
    path_is_file: bool
    title: str
    text: str
    modified: bool
    bookmarks: list[int]
    cursor: tuple[int, int]
    is_current: bool


@dataclass(frozen=True)
class RestoreFileOp:
    path: Path
    bookmarks: list[int]
    cursor: tuple[int, int] | None
    activate: bool


@dataclass(frozen=True)
class RestoreDraftOp:
    title: str
    text: str
    modified: bool
    bookmarks: list[int]
    cursor: tuple[int, int] | None
    activate: bool


def session_files_to_open(open_files: list[str], *, cap: int = RESTORE_FILE_CAP) -> list[Path]:
    """Existing files only, capped so restore cannot open N huge docs first."""
    out: list[Path] = []
    for raw in open_files[: max(0, cap)]:
        path = Path(raw)
        if path.is_file():
            out.append(path)
    return out


def collect_tabs_into_session(
    tabs: list[TabSessionView],
    base: SessionState,
    *,
    workspace: str | None,
    theme: str,
    language: str,
    word_wrap: bool,
    line_numbers: bool,
    icon_pack: str,
    geometry: Any = None,
    window_state: Any = None,
) -> SessionState:
    """Build a SessionState from tab snapshots + prefs already on ``base``."""
    open_files: list[str] = []
    bookmarks: dict[str, list[int]] = {}
    cursors: dict[str, tuple[int, int]] = {}
    drafts: list[dict[str, Any]] = []
    active: str | None = None
    for tab in tabs:
        if tab.path is not None and tab.path_is_file:
            p = normalize_path(tab.path)
            open_files.append(p)
            if tab.bookmarks:
                bookmarks[p] = list(tab.bookmarks)
            cursors[p] = tab.cursor
            if tab.is_current:
                active = p
            continue
        if not tab.text and not tab.modified:
            continue
        entry: dict[str, Any] = {
            "title": tab.title,
            "text": tab.text[:DRAFT_TEXT_CAP],
            "bookmarks": list(tab.bookmarks),
            "cursor": list(tab.cursor),
        }
        if tab.is_current:
            entry["active"] = True
        drafts.append(entry)
    return replace(
        base,
        theme=theme,
        language=language,
        word_wrap=word_wrap,
        line_numbers=line_numbers,
        workspace=workspace,
        open_files=open_files,
        active_file=active,
        bookmarks=bookmarks,
        cursors=cursors,
        drafts=drafts,
        icon_pack=icon_pack,
        geometry=geometry if geometry is not None else base.geometry,
        window_state=window_state if window_state is not None else base.window_state,
    )


def _lookup_marks(session: SessionState, path: Path) -> list[int]:
    key = normalize_path(path)
    marks = session.bookmarks.get(key) or session.bookmarks.get(str(path)) or []
    return [int(m) for m in marks]


def _lookup_cursor(session: SessionState, path: Path) -> tuple[int, int] | None:
    key = normalize_path(path)
    cur = session.cursors.get(key) or session.cursors.get(str(path))
    if cur is None or len(cur) < 2:
        return None
    return int(cur[0]), int(cur[1])


def plan_session_restore(
    session: SessionState,
) -> tuple[list[RestoreFileOp], list[RestoreDraftOp]]:
    """Turn persisted session into restore ops (files that still exist + drafts)."""
    active_key = normalize_path(session.active_file) if session.active_file else None
    files: list[RestoreFileOp] = []
    for path in session_files_to_open(session.open_files):
        key = normalize_path(path)
        files.append(
            RestoreFileOp(
                path=path,
                bookmarks=_lookup_marks(session, path),
                cursor=_lookup_cursor(session, path),
                activate=bool(active_key and key == active_key),
            )
        )
    drafts: list[RestoreDraftOp] = []
    for draft in session.drafts:
        text = str(draft.get("text") or "")
        title = str(draft.get("title") or "Untitled")
        marks = draft.get("bookmarks")
        bookmarks = [int(m) for m in marks] if isinstance(marks, list) else []
        cur = draft.get("cursor")
        cursor: tuple[int, int] | None = None
        if isinstance(cur, (list, tuple)) and len(cur) >= 2:
            try:
                cursor = (int(cur[0]), int(cur[1]))
            except (TypeError, ValueError):
                cursor = None
        drafts.append(
            RestoreDraftOp(
                title=title,
                text=text,
                modified=bool(text),
                bookmarks=bookmarks,
                cursor=cursor,
                activate=bool(draft.get("active")),
            )
        )
    return files, drafts

