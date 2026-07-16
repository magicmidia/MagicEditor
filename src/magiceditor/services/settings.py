"""Persistent user preferences and last-session state (QSettings)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from PyQt6.QtCore import QByteArray, QSettings


@dataclass
class SessionState:
    theme: str = "midnight_dark"
    language: str = "en_US"
    word_wrap: bool = False
    line_numbers: bool = True
    workspace: str | None = None
    open_files: list[str] = field(default_factory=list)
    active_file: str | None = None
    geometry: QByteArray | None = None
    window_state: QByteArray | None = None


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

    def load(self) -> SessionState:
        qs = self._qs
        files = qs.value("session/open_files", [])
        if isinstance(files, str):
            files = [files] if files else []
        elif not isinstance(files, list):
            files = list(files) if files else []
        open_files = [str(p) for p in files if p and Path(str(p)).is_file()]

        workspace = qs.value("session/workspace", "", str) or None
        if workspace and not Path(workspace).is_dir():
            workspace = None

        active = qs.value("session/active_file", "", str) or None
        if active and active not in open_files:
            active = open_files[0] if open_files else None

        geom = qs.value("window/geometry")
        state = qs.value("window/state")
        return SessionState(
            theme=qs.value("ui/theme", "midnight_dark", str) or "midnight_dark",
            language=qs.value("ui/language", "en_US", str) or "en_US",
            word_wrap=self._as_bool(qs.value("ui/word_wrap"), False),
            # Default ON when key is missing (first run / reset).
            line_numbers=(
                True
                if "ui/line_numbers" not in qs.allKeys()
                else self._as_bool(qs.value("ui/line_numbers"), True)
            ),
            workspace=workspace,
            open_files=open_files,
            active_file=active,
            geometry=geom if isinstance(geom, QByteArray) else None,
            window_state=state if isinstance(state, QByteArray) else None,
        )

    def save(self, state: SessionState) -> None:
        qs = self._qs
        qs.setValue("ui/theme", state.theme)
        qs.setValue("ui/language", state.language)
        qs.setValue("ui/word_wrap", state.word_wrap)
        qs.setValue("ui/line_numbers", state.line_numbers)
        qs.setValue("session/workspace", state.workspace or "")
        qs.setValue("session/open_files", state.open_files)
        qs.setValue("session/active_file", state.active_file or "")
        if state.geometry is not None:
            qs.setValue("window/geometry", state.geometry)
        if state.window_state is not None:
            qs.setValue("window/state", state.window_state)
        qs.sync()
