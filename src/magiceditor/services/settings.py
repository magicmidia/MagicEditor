"""Persistent user preferences and last-session state (QSettings)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QByteArray, QSettings


@dataclass
class SessionState:
    theme: str = "luminous_void"
    language: str = "en_US"
    word_wrap: bool = False
    line_numbers: bool = True
    workspace: str | None = None
    open_files: list[str] = field(default_factory=list)
    active_file: str | None = None
    # path -> 0-based line numbers
    bookmarks: dict[str, list[int]] = field(default_factory=dict)
    # path -> (line 1-based, column 1-based)
    cursors: dict[str, tuple[int, int]] = field(default_factory=dict)
    # Graphics / appearance
    gpu_acceleration: bool = True
    gpu_multisample: bool = True
    antialiasing: bool = True
    window_opacity: float = 1.0  # 0.55-1.0
    chrome_transparency: bool = False
    editor_transparency: bool = False
    geometry: QByteArray | None = None
    window_state: QByteArray | None = None


def normalize_path(path: str | Path) -> str:
    """Absolute resolved path string for stable session keys."""
    try:
        return str(Path(path).expanduser().resolve())
    except OSError:
        return str(path)


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

        geom = qs.value("window/geometry")
        state = qs.value("window/state")
        return SessionState(
            theme=qs.value("ui/theme", "luminous_void", str) or "luminous_void",
            language=qs.value("ui/language", "en_US", str) or "en_US",
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
            gpu_acceleration=self._as_bool(qs.value("graphics/gpu_acceleration"), True),
            gpu_multisample=self._as_bool(qs.value("graphics/gpu_multisample"), True),
            antialiasing=self._as_bool(qs.value("graphics/antialiasing"), True),
            window_opacity=opacity_f,
            chrome_transparency=self._as_bool(qs.value("graphics/chrome_transparency"), False),
            editor_transparency=self._as_bool(qs.value("graphics/editor_transparency"), False),
            geometry=geom if isinstance(geom, QByteArray) else None,
            window_state=state if isinstance(state, QByteArray) else None,
        )

    def save(self, state: SessionState) -> None:
        qs = self._qs
        qs.setValue("ui/theme", state.theme)
        qs.setValue("ui/language", state.language)
        qs.setValue("ui/word_wrap", state.word_wrap)
        qs.setValue("ui/line_numbers", state.line_numbers)
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

        if state.geometry is not None:
            qs.setValue("window/geometry", state.geometry)
        if state.window_state is not None:
            qs.setValue("window/state", state.window_state)
        qs.sync()
