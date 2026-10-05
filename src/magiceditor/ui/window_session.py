"""Session restore / collect helpers (J1.2) — no widget I/O policy."""

from __future__ import annotations

from collections.abc import Iterable
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
    recovery_text: str | None = None


@dataclass(frozen=True)
class RestoreDraftOp:
    title: str
    text: str
    modified: bool
    bookmarks: list[int]
    cursor: tuple[int, int] | None
    activate: bool


@dataclass(frozen=True)
class RestoreGroupOp:
    name: str
    color: str | None
    collapsed: bool
    member_indices: list[int]


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
    tab_groups: list[dict[str, Any]] | None = None,
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
            if tab.modified:
                entry = {
                    "title": tab.title,
                    "text": tab.text[:DRAFT_TEXT_CAP],
                    "bookmarks": list(tab.bookmarks),
                    "cursor": list(tab.cursor),
                    "path": p,
                }
                if tab.is_current:
                    entry["active"] = True
                drafts.append(entry)
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
        tab_groups=tab_groups if tab_groups is not None else base.tab_groups,
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


def _draft_marks(draft: dict[str, Any]) -> list[int]:
    marks = draft.get("bookmarks")
    if not isinstance(marks, list):
        return []
    out: list[int] = []
    for m in marks:
        try:
            out.append(int(m))
        except (TypeError, ValueError):
            continue
    return out


def _draft_cursor(draft: dict[str, Any]) -> tuple[int, int] | None:
    cur = draft.get("cursor")
    if not isinstance(cur, (list, tuple)) or len(cur) < 2:
        return None
    try:
        return int(cur[0]), int(cur[1])
    except (TypeError, ValueError):
        return None


def _draft_op(draft: dict[str, Any], *, modified: bool | None = None) -> RestoreDraftOp:
    text = str(draft.get("text") or "")[:DRAFT_TEXT_CAP]
    return RestoreDraftOp(
        title=str(draft.get("title") or "Untitled"),
        text=text,
        modified=bool(text) if modified is None else modified,
        bookmarks=_draft_marks(draft),
        cursor=_draft_cursor(draft),
        activate=bool(draft.get("active")),
    )


def plan_session_restore(
    session: SessionState,
) -> tuple[list[RestoreFileOp], list[RestoreDraftOp]]:
    """Turn persisted session into restore ops (files that still exist + drafts).

    A draft with ``path`` is unsaved text for that file. It is attached as
    ``recovery_text`` when the file is opened, and becomes an untitled draft
    when the file is gone so the text is not dropped. The file on disk is not
    overwritten here.
    """
    active_key = normalize_path(session.active_file) if session.active_file else None
    recovery_by_path: dict[str, dict[str, Any]] = {}
    untitled: list[dict[str, Any]] = []
    for draft in session.drafts:
        if not isinstance(draft, dict):
            continue
        raw_path = draft.get("path")
        if isinstance(raw_path, str) and raw_path.strip():
            recovery_by_path[normalize_path(raw_path)] = draft
        else:
            untitled.append(draft)

    candidates: list[Path] = list(session_files_to_open(session.open_files))
    seen = {normalize_path(p) for p in candidates}
    for key in recovery_by_path:
        if key in seen or not Path(key).is_file():
            continue
        if len(candidates) >= RESTORE_FILE_CAP:
            break
        candidates.append(Path(key))
        seen.add(key)

    files: list[RestoreFileOp] = []
    consumed: set[str] = set()
    for path in candidates:
        key = normalize_path(path)
        draft = recovery_by_path.get(key)
        marks = _lookup_marks(session, path)
        cursor = _lookup_cursor(session, path)
        recovery_text: str | None = None
        if draft is not None:
            recovery_text = str(draft.get("text") or "")[:DRAFT_TEXT_CAP]
            consumed.add(key)
            if not marks:
                marks = _draft_marks(draft)
            if cursor is None:
                cursor = _draft_cursor(draft)
        activate = bool(active_key and key == active_key)
        if not activate and active_key is None and draft is not None and draft.get("active"):
            activate = True
        files.append(
            RestoreFileOp(
                path=path,
                bookmarks=marks,
                cursor=cursor,
                activate=activate,
                recovery_text=recovery_text,
            )
        )

    drafts: list[RestoreDraftOp] = [_draft_op(item) for item in untitled]
    for key, draft in recovery_by_path.items():
        if key in consumed or Path(key).is_file():
            continue
        text = str(draft.get("text") or "")
        if not text:
            continue
        drafts.append(_draft_op(draft, modified=True))
    return files, drafts



def collect_tab_groups(groups: Iterable[Any], member_keys: dict[int, str]) -> list[dict[str, Any]]:
    """Serialize TabGroup-like objects; members become path-or-title keys.

    ``member_keys`` maps ``id(widget)`` → normalized path (file-backed tab) or
    document title (untitled). Groups with no resolvable members are dropped.
    """
    out: list[dict[str, Any]] = []
    for g in groups:
        members = [member_keys[m] for m in g.members if m in member_keys]
        if not members:
            continue
        out.append(
            {
                "name": str(g.name),
                "color": str(g.color),
                "collapsed": bool(g.collapsed),
                "members": members,
            }
        )
    return out


def plan_group_restore(
    tab_groups: list[dict[str, Any]],
    available_keys: list[str],
) -> list[RestoreGroupOp]:
    """Match persisted member keys to restored tabs (positions in ``available_keys``).

    Members without a match are ignored; groups with no matched members are skipped.
    """
    key_to_index: dict[str, int] = {}
    for i, key in enumerate(available_keys):
        if key:
            key_to_index.setdefault(key, i)
    ops: list[RestoreGroupOp] = []
    for item in tab_groups:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        members_raw = item.get("members")
        if not name or not isinstance(members_raw, list):
            continue
        indices = [
            key_to_index[m]
            for m in members_raw
            if isinstance(m, str) and m in key_to_index
        ]
        if not indices:
            continue
        ops.append(
            RestoreGroupOp(
                name=name,
                color=str(item.get("color") or "") or None,
                collapsed=bool(item.get("collapsed")),
                member_indices=indices,
            )
        )
    return ops
