"""AppSettings persistence tests."""

from __future__ import annotations

from pathlib import Path

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
