"""AppSettings persistence tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from PyQt6.QtCore import QSettings

from magiceditor.services.settings import AppSettings, SessionState, normalize_path


def _isolated(tmp_path: Path) -> AppSettings:
    ini = tmp_path / "settings.ini"
    qs = QSettings(str(ini), QSettings.Format.IniFormat)
    return AppSettings(settings=qs)


def test_settings_roundtrip(tmp_path: Path) -> None:
    s = _isolated(tmp_path)
    state = SessionState(
        theme="darcula",
        language="pt_BR",
        word_wrap=True,
        line_numbers=False,
        open_files=[],
        active_file=None,
    )
    s.save(state)
    loaded = s.load()
    assert loaded.theme == "darcula"
    assert loaded.language == "pt_BR"
    assert loaded.word_wrap is True
    assert loaded.line_numbers is False


def test_open_files_and_bookmarks_roundtrip(tmp_path: Path) -> None:
    f1 = tmp_path / "a.py"
    f2 = tmp_path / "b.py"
    f1.write_text("print(1)\n", encoding="utf-8")
    f2.write_text("print(2)\n", encoding="utf-8")
    p1 = normalize_path(f1)
    p2 = normalize_path(f2)

    s = _isolated(tmp_path)
    state = SessionState(
        theme="midnight_dark",
        language="en_US",
        open_files=[p1, p2],
        active_file=p2,
        bookmarks={p1: [0, 2], p2: [1]},
        cursors={p1: (1, 1), p2: (2, 5)},
        workspace=str(tmp_path),
    )
    s.save(state)
    loaded = s.load()
    assert loaded.open_files == [p1, p2]
    assert loaded.active_file == p2
    assert loaded.bookmarks[p1] == [0, 2]
    assert loaded.bookmarks[p2] == [1]
    assert loaded.cursors[p2] == (2, 5)
    assert loaded.workspace is not None
    assert Path(loaded.workspace).resolve() == tmp_path.resolve()


def test_drafts_and_recent_roundtrip(tmp_path: Path) -> None:
    f1 = tmp_path / "recent.py"
    f1.write_text("x=1\n", encoding="utf-8")
    p1 = normalize_path(f1)
    s = _isolated(tmp_path)
    state = SessionState(
        drafts=[
            {
                "title": "Untitled-1",
                "text": "hello draft",
                "active": True,
                "bookmarks": [0],
                "cursor": [1, 3],
            }
        ],
        recent_files=[p1],
        theme="luminous_void",
    )
    s.save(state)
    loaded = s.load()
    assert len(loaded.drafts) == 1
    assert loaded.drafts[0]["text"] == "hello draft"
    assert loaded.drafts[0]["title"] == "Untitled-1"
    assert loaded.recent_files == [p1]


def test_graphics_prefs_roundtrip(tmp_path: Path) -> None:
    s = _isolated(tmp_path)
    state = SessionState(
        gpu_acceleration=False,
        gpu_multisample=False,
        antialiasing=True,
        window_opacity=0.85,
        chrome_transparency=True,
        editor_transparency=True,
        theme="luminous_void",
    )
    s.save(state)
    loaded = s.load()
    assert loaded.gpu_acceleration is False
    assert loaded.gpu_multisample is False
    assert loaded.window_opacity == pytest.approx(0.85)
    assert loaded.chrome_transparency is True
    assert loaded.editor_transparency is True
    assert loaded.theme == "luminous_void"


def test_editor_and_chrome_prefs_roundtrip(tmp_path: Path) -> None:
    s = _isolated(tmp_path)
    state = SessionState(
        font_size=16,
        tab_width=2,
        indent_with_spaces=False,
        highlight_current_line=False,
        restore_session=False,
        open_in_existing_window=False,
        show_status_bar=False,
        show_toolbar=False,
        word_wrap=True,
        line_numbers=False,
        icon_pack="material",
        theme="darcula",
    )
    s.save(state)
    loaded = s.load()
    assert loaded.font_size == 16
    assert loaded.tab_width == 2
    assert loaded.indent_with_spaces is False
    assert loaded.highlight_current_line is False
    assert loaded.restore_session is False
    assert loaded.open_in_existing_window is False
    assert loaded.show_status_bar is False
    assert loaded.show_toolbar is False
    assert loaded.word_wrap is True
    assert loaded.line_numbers is False
    assert loaded.icon_pack == "material"


def test_draft_path_and_editor_prefs_roundtrip(tmp_path: Path) -> None:
    target = tmp_path / "note.txt"
    target.write_text("disk\n", encoding="utf-8")
    path = normalize_path(target)
    s = _isolated(tmp_path)
    s.save(
        SessionState(
            drafts=[{"title": "note.txt", "text": "unsaved", "path": path, "active": True}],
            open_files=[path],
            active_file=path,
            recovery_interval_sec=12,
            line_spacing=4,
            indent_guides=True,
            auto_close_brackets=True,
            right_margin=80,
            highlight_occurrences=True,
            wheel_zoom=False,
        )
    )
    loaded = s.load()
    assert loaded.drafts[0]["path"] == path
    assert loaded.drafts[0]["text"] == "unsaved"
    assert loaded.recovery_interval_sec == 12
    assert loaded.line_spacing == 4
    assert loaded.indent_guides is True
    assert loaded.auto_close_brackets is True
    assert loaded.right_margin == 80
    assert loaded.highlight_occurrences is True
    assert loaded.wheel_zoom is False
    assert s.recovery_path().parent == tmp_path
    assert s.recovery_path().is_file()


def test_recovery_file_overrides_stale_drafts(tmp_path: Path) -> None:
    from magiceditor.services.recovery_store import write_recovery

    s = _isolated(tmp_path)
    s.save(SessionState(drafts=[{"title": "Old", "text": "stale"}]))
    write_recovery(
        s.recovery_path(),
        {
            "version": 1,
            "open_files": [],
            "active_file": None,
            "drafts": [{"title": "New", "text": "fresh"}],
            "bookmarks": {},
            "cursors": {},
        },
    )
    loaded = s.load()
    assert loaded.drafts[0]["text"] == "fresh"


def test_empty_recovery_does_not_resurrect_drafts(tmp_path: Path) -> None:
    from magiceditor.services.recovery_store import write_recovery

    s = _isolated(tmp_path)
    s.save(SessionState(drafts=[{"title": "U", "text": "keep"}]))
    write_recovery(
        s.recovery_path(),
        {
            "version": 1,
            "open_files": [],
            "active_file": None,
            "drafts": [],
            "bookmarks": {},
            "cursors": {},
        },
    )
    loaded = s.load()
    assert loaded.drafts == []
    assert loaded.open_files == []


def test_missing_files_dropped_on_load(tmp_path: Path) -> None:
    gone = tmp_path / "missing.txt"
    # do not create
    s = _isolated(tmp_path)
    s.save(
        SessionState(
            open_files=[str(gone)],
            active_file=str(gone),
            bookmarks={str(gone): [0]},
        )
    )
    loaded = s.load()
    assert loaded.open_files == []
    assert loaded.active_file is None
