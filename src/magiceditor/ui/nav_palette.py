"""Command / minimap / theme-bundle helpers (J1.3 / N8)."""

from __future__ import annotations

from magiceditor.services.theme_io import parse_theme_bundle, theme_bundle_dict

__all__ = [
    "autosave_interval_ms",
    "goto_anything_file_list",
    "minimap_status_state",
    "palette_entries_from_actions",
    "parse_theme_bundle",
    "split_view_text",
    "theme_bundle_dict",
]


def minimap_status_state(enabled: bool) -> str:
    return "on" if enabled else "off"


def split_view_text(buffer_len: int, text: str, *, cap: int = 2_000_000) -> str:
    if buffer_len >= 5_000_000:
        return "(huge file - use main pane)"
    return text[:cap]


def autosave_interval_ms(seconds: int) -> int:
    sec = int(seconds or 0)
    return sec * 1000 if sec > 0 else 0


def palette_entries_from_actions(actions: dict) -> list[tuple[str, str, str]]:
    """(id, label, shortcut) for the command palette — no Qt callbacks."""
    out: list[tuple[str, str, str]] = []
    for key, act in actions.items():
        label = (act.text() or key).replace("&", "")
        shortcut = ""
        sc = act.shortcut()
        if sc:
            shortcut = sc.toString()
        out.append((key, label, shortcut))
    return out


def goto_anything_file_list(recent: list[str], open_paths: list[str]) -> list[str]:
    seen: set[str] = set()
    files: list[str] = []
    for p in [*recent, *open_paths]:
        if p and p not in seen:
            seen.add(p)
            files.append(p)
    return files
