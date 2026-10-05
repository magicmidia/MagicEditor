"""Persistent user preferences and last-session state (QSettings)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QByteArray, QSettings

from magiceditor.services.recovery_store import (
    RECOVERY_VERSION,
    apply_recovery,
    normalize_drafts,
    read_recovery,
    write_recovery,
)
from magiceditor.services.session_state import SessionState, normalize_path
from magiceditor.services.settings_clamp import clamp_int as _clamp_int

__all__ = ["AppSettings", "SessionState", "normalize_path"]

# Caps for session drafts (Untitled + dirty-file recovery)
_MAX_DRAFTS = 24
_MAX_DRAFT_CHARS = 400_000
_MAX_RECENT = 15


class AppSettings:
    """Load/save preferences under org MagicEditor / app MagicEditor."""

    def __init__(
        self,
        *,
        settings: QSettings | None = None,
        organization: str = "MagicEditor",
        application: str = "MagicEditor",
    ) -> None:
        # ``settings`` allows tests to inject an isolated QSettings (e.g. IniFormat + temp path).
        self._qs = settings if settings is not None else QSettings(organization, application)

    @staticmethod
    def _as_bool(value: object, default: bool = False) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return default

    @staticmethod
    def _as_str_list(value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value] if value else []
        if isinstance(value, list):
            return [str(p) for p in value if p]
        try:
            return [str(p) for p in list(value) if p]
        except TypeError:
            return []

    @staticmethod
    def _load_json_dict(raw: object) -> dict[str, Any]:
        if not raw:
            return {}
        if isinstance(raw, dict):
            return {str(k): v for k, v in raw.items()}
        if isinstance(raw, str):
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                return {}
            if isinstance(data, dict):
                return {str(k): v for k, v in data.items()}
        return {}

    @staticmethod
    def _load_json_list(raw: object) -> list[Any]:
        if not raw:
            return []
        if isinstance(raw, list):
            return list(raw)
        if isinstance(raw, str):
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                return []
            if isinstance(data, list):
                return list(data)
        return []

    def load(self) -> SessionState:
        qs = self._qs
        raw_files = self._as_str_list(qs.value("session/open_files", []))
        open_files: list[str] = []
        seen: set[str] = set()
        for p in raw_files:
            path = Path(p)
            if not path.is_file():
                continue
            key = normalize_path(path)
            if key in seen:
                continue
            seen.add(key)
            open_files.append(key)

        workspace = qs.value("session/workspace", "", str) or None
        if workspace and not Path(workspace).is_dir():
            workspace = None
        elif workspace:
            workspace = normalize_path(workspace)

        active_raw = qs.value("session/active_file", "", str) or None
        active: str | None = None
        if active_raw:
            active_norm = normalize_path(active_raw) if Path(active_raw).is_file() else active_raw
            if active_norm in open_files:
                active = active_norm
            else:
                # try match by resolve
                for f in open_files:
                    if f == active_norm or Path(f).name == Path(active_raw).name:
                        active = f
                        break
        if active is None and open_files:
            active = open_files[0]

        bookmarks: dict[str, list[int]] = {}
        for key, lines in self._load_json_dict(qs.value("session/bookmarks_json", "")).items():
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
            if cleaned:
                nkey = normalize_path(key) if Path(key).exists() else key
                bookmarks[nkey] = cleaned

        cursors: dict[str, tuple[int, int]] = {}
        for key, pos in self._load_json_dict(qs.value("session/cursors_json", "")).items():
            if not isinstance(pos, (list, tuple)) or len(pos) < 2:
                continue
            try:
                line, col = int(pos[0]), int(pos[1])
            except (TypeError, ValueError):
                continue
            line = max(line, 1)
            col = max(col, 1)
            nkey = normalize_path(key) if Path(key).exists() else key
            cursors[nkey] = (line, col)

        opacity = qs.value("graphics/window_opacity", 1.0)
        try:
            opacity_f = float(opacity)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            opacity_f = 1.0
        opacity_f = max(0.55, min(1.0, opacity_f))

        drafts = normalize_drafts(
            self._load_json_list(qs.value("session/drafts_json", "")),
            limit=_MAX_DRAFTS,
            max_chars=_MAX_DRAFT_CHARS,
        )

        tab_groups: list[dict[str, Any]] = []
        for item in self._load_json_list(qs.value("session/tab_groups_json", "")):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            members_raw = item.get("members")
            members = (
                [str(m) for m in members_raw if isinstance(m, str) and m]
                if isinstance(members_raw, list)
                else []
            )
            tab_groups.append(
                {
                    "name": name,
                    "color": str(item.get("color") or ""),
                    "collapsed": bool(item.get("collapsed")),
                    "members": members,
                }
            )

        recent: list[str] = []
        seen_r: set[str] = set()
        for p in self._as_str_list(qs.value("session/recent_files", [])):
            path = Path(p)
            if not path.is_file():
                continue
            key = normalize_path(path)
            if key in seen_r:
                continue
            seen_r.add(key)
            recent.append(key)
            if len(recent) >= _MAX_RECENT:
                break

        geom = qs.value("window/geometry")
        win_state = qs.value("window/state")
        loaded = SessionState(
            theme=qs.value("ui/theme", "luminous_void", str) or "luminous_void",
            language=qs.value("ui/language", "pt_BR", str) or "pt_BR",
            word_wrap=self._as_bool(qs.value("ui/word_wrap"), False),
            line_numbers=(
                True
                if "ui/line_numbers" not in qs.allKeys()
                else self._as_bool(qs.value("ui/line_numbers"), True)
            ),
            workspace=workspace,
            open_files=open_files,
            active_file=active,
            bookmarks=bookmarks,
            cursors=cursors,
            drafts=drafts,
            tab_groups=tab_groups,
            recent_files=recent,
            icon_pack=qs.value("ui/icon_pack", "qlementine", str) or "qlementine",
            font_size=_clamp_int(qs.value("editor/font_size", 12), 8, 48, 12),
            tab_width=_clamp_int(qs.value("editor/tab_width", 4), 2, 8, 4),
            indent_with_spaces=self._as_bool(qs.value("editor/indent_with_spaces"), True),
            highlight_current_line=self._as_bool(qs.value("editor/highlight_current_line"), True),
            restore_session=self._as_bool(qs.value("ui/restore_session"), True),
            open_in_existing_window=self._as_bool(qs.value("ui/open_in_existing_window"), True),
            show_status_bar=self._as_bool(qs.value("ui/show_status_bar"), True),
            show_toolbar=self._as_bool(qs.value("ui/show_toolbar"), True),
            show_splash=self._as_bool(qs.value("ui/show_splash"), True),
            spell_check=self._as_bool(qs.value("editor/spell_check"), True),
            spell_language=qs.value("editor/spell_language", "pt_BR", str) or "pt_BR",
            spell_force=(True if self._as_bool(qs.value("editor/spell_force"), False) else None),
            spell_extra_languages=qs.value("editor/spell_extra", "", str) or "",
            autosave_interval_sec=_clamp_int(qs.value("editor/autosave_sec", 0), 0, 3600, 0),
            recovery_interval_sec=_clamp_int(qs.value("editor/recovery_sec"), 2, 120, 8),
            line_spacing=_clamp_int(qs.value("editor/line_spacing"), 0, 16, 0),
            indent_guides=self._as_bool(qs.value("editor/indent_guides"), False),
            auto_close_brackets=self._as_bool(qs.value("editor/auto_close_brackets"), False),
            right_margin=_clamp_int(qs.value("editor/right_margin"), 0, 240, 0),
            highlight_occurrences=self._as_bool(qs.value("editor/highlight_occurrences"), False),
            wheel_zoom=self._as_bool(qs.value("editor/wheel_zoom"), True),
            show_minimap=self._as_bool(qs.value("ui/show_minimap"), False),
            first_run_done=self._as_bool(qs.value("ui/first_run_done"), False),
            want_file_associations=self._as_bool(qs.value("ui/want_file_associations"), False),
            high_contrast=self._as_bool(qs.value("ui/high_contrast"), False),
            word_completion=self._as_bool(qs.value("editor/word_completion"), False),
            show_whitespace=self._as_bool(qs.value("editor/show_whitespace"), False),
            brace_match=self._as_bool(qs.value("editor/brace_match"), True),
            syntax_highlight=self._as_bool(qs.value("editor/syntax_highlight"), True),
            caret_width=_clamp_int(qs.value("editor/caret_width", 1), 1, 4, 1),
            trim_trailing_on_save=self._as_bool(qs.value("editor/trim_trailing_on_save"), False),
            insert_final_newline=self._as_bool(qs.value("editor/insert_final_newline"), False),
            editor_context_menu=self._as_bool(qs.value("editor/context_menu"), True),
            tab_height=_clamp_int(qs.value("tabs/height", 30), 22, 40, 30),
            tab_min_width=_clamp_int(qs.value("tabs/min_width", 72), 48, 160, 72),
            tab_max_width=_clamp_int(qs.value("tabs/max_width", 220), 120, 400, 220),
            show_tab_scroll_buttons=self._as_bool(qs.value("tabs/scroll_buttons"), True),
            middle_click_close=self._as_bool(qs.value("tabs/middle_click_close"), True),
            confirm_close_unsaved=self._as_bool(qs.value("tabs/confirm_close_unsaved"), True),
            recent_files_max=_clamp_int(qs.value("session/recent_max", 15), 5, 50, 15),
            gpu_acceleration=self._as_bool(qs.value("graphics/gpu_acceleration"), True),
            gpu_multisample=self._as_bool(qs.value("graphics/gpu_multisample"), True),
            antialiasing=self._as_bool(qs.value("graphics/antialiasing"), True),
            window_opacity=opacity_f,
            chrome_transparency=self._as_bool(qs.value("graphics/chrome_transparency"), False),
            editor_transparency=self._as_bool(qs.value("graphics/editor_transparency"), False),
            geometry=geom if isinstance(geom, QByteArray) else None,
            window_state=win_state if isinstance(win_state, QByteArray) else None,
        )
        payload = read_recovery(self.recovery_path())
        if payload is not None:
            loaded = apply_recovery(loaded, payload)
        return loaded

    def save(self, state: SessionState) -> None:
        qs = self._qs
        qs.setValue("ui/theme", state.theme)
        qs.setValue("ui/language", state.language)
        qs.setValue("ui/word_wrap", state.word_wrap)
        qs.setValue("ui/line_numbers", state.line_numbers)
        qs.setValue("ui/icon_pack", state.icon_pack or "qlementine")
        qs.setValue("editor/font_size", int(max(8, min(48, state.font_size))))
        qs.setValue("editor/tab_width", int(max(2, min(8, state.tab_width))))
        qs.setValue("editor/indent_with_spaces", state.indent_with_spaces)
        qs.setValue("editor/highlight_current_line", state.highlight_current_line)
        qs.setValue("ui/restore_session", state.restore_session)
        qs.setValue("ui/open_in_existing_window", state.open_in_existing_window)
        qs.setValue("ui/show_status_bar", state.show_status_bar)
        qs.setValue("ui/show_toolbar", state.show_toolbar)
        qs.setValue("ui/show_splash", state.show_splash)
        qs.setValue("editor/spell_check", state.spell_check)
        qs.setValue("editor/spell_language", state.spell_language or "pt_BR")
        qs.setValue("editor/spell_force", bool(state.spell_force) is True)
        qs.setValue("editor/spell_extra", state.spell_extra_languages or "")
        qs.setValue("editor/autosave_sec", int(max(0, min(3600, state.autosave_interval_sec))))
        qs.setValue("editor/recovery_sec", int(max(2, min(120, state.recovery_interval_sec))))
        qs.setValue("editor/line_spacing", int(max(0, min(16, state.line_spacing))))
        qs.setValue("editor/indent_guides", state.indent_guides)
        qs.setValue("editor/auto_close_brackets", state.auto_close_brackets)
        qs.setValue("editor/right_margin", int(max(0, min(240, state.right_margin))))
        qs.setValue("editor/highlight_occurrences", state.highlight_occurrences)
        qs.setValue("editor/wheel_zoom", state.wheel_zoom)
        qs.setValue("ui/show_minimap", state.show_minimap)
        qs.setValue("ui/first_run_done", state.first_run_done)
        qs.setValue("ui/want_file_associations", state.want_file_associations)
        qs.setValue("ui/high_contrast", state.high_contrast)
        qs.setValue("editor/word_completion", state.word_completion)
        qs.setValue("editor/show_whitespace", state.show_whitespace)
        qs.setValue("editor/brace_match", state.brace_match)
        qs.setValue("editor/syntax_highlight", state.syntax_highlight)
        qs.setValue("editor/caret_width", int(max(1, min(4, state.caret_width))))
        qs.setValue("editor/trim_trailing_on_save", state.trim_trailing_on_save)
        qs.setValue("editor/insert_final_newline", state.insert_final_newline)
        qs.setValue("editor/context_menu", state.editor_context_menu)
        qs.setValue("tabs/height", int(max(22, min(40, state.tab_height))))
        qs.setValue("tabs/min_width", int(max(48, min(160, state.tab_min_width))))
        qs.setValue("tabs/max_width", int(max(120, min(400, state.tab_max_width))))
        qs.setValue("tabs/scroll_buttons", state.show_tab_scroll_buttons)
        qs.setValue("tabs/middle_click_close", state.middle_click_close)
        qs.setValue("tabs/confirm_close_unsaved", state.confirm_close_unsaved)
        qs.setValue("session/recent_max", int(max(5, min(50, state.recent_files_max))))
        qs.setValue("graphics/gpu_acceleration", state.gpu_acceleration)
        qs.setValue("graphics/gpu_multisample", state.gpu_multisample)
        qs.setValue("graphics/antialiasing", state.antialiasing)
        qs.setValue("graphics/window_opacity", float(state.window_opacity))
        qs.setValue("graphics/chrome_transparency", state.chrome_transparency)
        qs.setValue("graphics/editor_transparency", state.editor_transparency)
        qs.setValue("session/workspace", state.workspace or "")
        # Store absolute paths only; drop missing files at save time too
        files: list[str] = []
        for p in state.open_files:
            path = Path(p)
            if path.is_file():
                files.append(normalize_path(path))
        qs.setValue("session/open_files", files)
        active = state.active_file
        if active:
            active = normalize_path(active) if Path(active).is_file() else active
            if active not in files:
                active = files[0] if files else ""
        qs.setValue("session/active_file", active or "")

        bookmarks_out: dict[str, list[int]] = {}
        for k, v in state.bookmarks.items():
            if not v:
                continue
            lines: list[int] = []
            for x in v:
                try:
                    n = int(x)
                except (TypeError, ValueError):
                    continue
                if n >= 0:
                    lines.append(n)
            if lines:
                nkey = normalize_path(k) if Path(k).exists() else k
                bookmarks_out[nkey] = sorted(set(lines))
        qs.setValue("session/bookmarks_json", json.dumps(bookmarks_out, separators=(",", ":")))

        cursors_out: dict[str, list[int]] = {}
        for k, (line, col) in state.cursors.items():
            key = normalize_path(k) if Path(k).exists() else k
            cursors_out[key] = [max(1, int(line)), max(1, int(col))]
        qs.setValue("session/cursors_json", json.dumps(cursors_out, separators=(",", ":")))

        drafts_out = normalize_drafts(state.drafts, limit=_MAX_DRAFTS, max_chars=_MAX_DRAFT_CHARS)
        qs.setValue("session/drafts_json", json.dumps(drafts_out, separators=(",", ":")))

        tab_groups_out: list[dict[str, Any]] = []
        for item in state.tab_groups:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            members_raw = item.get("members")
            members = (
                [str(m) for m in members_raw if isinstance(m, str) and m]
                if isinstance(members_raw, list)
                else []
            )
            if not members:
                continue
            tab_groups_out.append(
                {
                    "name": name[:80],
                    "color": str(item.get("color") or ""),
                    "collapsed": bool(item.get("collapsed")),
                    "members": members[:64],
                }
            )
        qs.setValue("session/tab_groups_json", json.dumps(tab_groups_out, separators=(",", ":")))

        recent_out: list[str] = []
        seen_r: set[str] = set()
        for p in state.recent_files:
            path = Path(p)
            if not path.is_file():
                continue
            key = normalize_path(path)
            if key in seen_r:
                continue
            seen_r.add(key)
            recent_out.append(key)
            if len(recent_out) >= _MAX_RECENT:
                break
        qs.setValue("session/recent_files", recent_out)

        if state.geometry is not None:
            qs.setValue("window/geometry", state.geometry)
        if state.window_state is not None:
            qs.setValue("window/state", state.window_state)
        try:
            write_recovery(
                self.recovery_path(),
                {
                    "version": RECOVERY_VERSION,
                    "open_files": files,
                    "active_file": active or None,
                    "drafts": drafts_out,
                    "bookmarks": bookmarks_out,
                    "cursors": cursors_out,
                },
            )
        except OSError:
            pass
        qs.sync()

    def recovery_path(self) -> Path:
        """Sidecar beside an ini file; AppConfigLocation when settings are in the registry."""
        name = str(self._qs.fileName() or "")
        registry = (
            not name
            or name.upper().startswith("HKEY")
            or name.startswith("\\")
            or name.startswith("//")
        )
        if registry:
            from PyQt6.QtCore import QStandardPaths

            base = QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.AppConfigLocation
            )
            return Path(base) / "recovery.json"
        return Path(name).with_name("recovery.json")
