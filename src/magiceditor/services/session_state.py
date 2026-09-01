"""Session/preferences value object (J1.6) — no I/O."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QByteArray


@dataclass
class SessionState:
    theme: str = "luminous_void"
    language: str = "pt_BR"
    word_wrap: bool = False
    line_numbers: bool = True
    workspace: str | None = None
    open_files: list[str] = field(default_factory=list)
    active_file: str | None = None
    bookmarks: dict[str, list[int]] = field(default_factory=dict)
    cursors: dict[str, tuple[int, int]] = field(default_factory=dict)
    drafts: list[dict[str, Any]] = field(default_factory=list)
    recent_files: list[str] = field(default_factory=list)
    icon_pack: str = "qlementine"
    font_size: int = 12
    tab_width: int = 4
    indent_with_spaces: bool = True
    highlight_current_line: bool = True
    restore_session: bool = True
    open_in_existing_window: bool = True
    show_status_bar: bool = True
    show_toolbar: bool = True
    show_splash: bool = True
    spell_check: bool = True
    spell_language: str = "pt_BR"
    spell_force: bool | None = None
    spell_extra_languages: str = ""
    autosave_interval_sec: int = 0
    show_minimap: bool = False
    first_run_done: bool = False
    want_file_associations: bool = False
    high_contrast: bool = False
    word_completion: bool = False
    show_whitespace: bool = False
    brace_match: bool = True
    syntax_highlight: bool = True
    caret_width: int = 1
    trim_trailing_on_save: bool = False
    insert_final_newline: bool = False
    editor_context_menu: bool = True
    tab_height: int = 30
    tab_min_width: int = 72
    tab_max_width: int = 220
    show_tab_scroll_buttons: bool = True
    middle_click_close: bool = True
    confirm_close_unsaved: bool = True
    recent_files_max: int = 15
    gpu_acceleration: bool = True
    gpu_multisample: bool = True
    antialiasing: bool = True
    window_opacity: float = 1.0
    chrome_transparency: bool = False
    editor_transparency: bool = False
    geometry: QByteArray | None = None
    window_state: QByteArray | None = None


def normalize_path(path: str | Path) -> str:
    try:
        return str(Path(path).expanduser().resolve())
    except OSError:
        return str(path)
