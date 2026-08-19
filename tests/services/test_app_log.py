from __future__ import annotations

import logging
import warnings
from pathlib import Path

from magiceditor.paths import log_file_path, user_data_dir
from magiceditor.services.app_log import setup_logging


def test_log_file_path_is_root_magic_editor_log() -> None:
    path = log_file_path()
    assert path.name == "MagicEditor.log"
    assert path.is_absolute()


def test_setup_logging_writes_errors_and_warnings(tmp_path: Path) -> None:
    dest = tmp_path / "MagicEditor.log"
    setup_logging(dest)
    log = logging.getLogger("magiceditor.test_app_log")
    log.warning("sample-warning")
    log.error("sample-error")
    warnings.warn("sample-py-warning", UserWarning, stacklevel=1)
    logging.getLogger("magiceditor").error("uncaught-sim")

    text = dest.read_text(encoding="utf-8")
    assert "Logging started" in text
    assert "sample-warning" in text
    assert "sample-error" in text
    assert dest.name == "MagicEditor.log"


def test_excepthook_records_traceback(tmp_path: Path) -> None:
    dest = tmp_path / "MagicEditor.log"
    setup_logging(dest)
    import sys

    try:
        raise RuntimeError("hook-boom")
    except RuntimeError:
        sys.excepthook(*sys.exc_info())

    text = dest.read_text(encoding="utf-8")
    assert "hook-boom" in text
    assert "RuntimeError" in text


def test_frozen_installed_log_is_not_under_program_files(tmp_path: Path) -> None:
    pf = tmp_path / "Program Files" / "MagicEditor"
    pf.mkdir(parents=True)
    local = tmp_path / "LocalAppData"
    dest = log_file_path(frozen=True, exe_dir=pf, local_app_data=local)
    assert dest == local / "MagicEditor" / "MagicEditor.log"
    assert "Program Files" not in dest.parts


def test_frozen_portable_log_stays_beside_exe(tmp_path: Path) -> None:
    root = tmp_path / "usb"
    root.mkdir()
    (root / "portable.ini").write_text("1", encoding="utf-8")
    dest = log_file_path(frozen=True, exe_dir=root, local_app_data=tmp_path / "Local")
    assert dest == root / "MagicEditor.log"


def test_user_data_dir_uses_localappdata(tmp_path: Path) -> None:
    assert user_data_dir(local_app_data=tmp_path) == tmp_path / "MagicEditor"


def test_setup_logging_falls_back_when_preferred_unwritable(tmp_path: Path, monkeypatch) -> None:
    blocked = tmp_path / "blocked"
    blocked.mkdir()
    fallback_dir = tmp_path / "AppData" / "MagicEditor"
    monkeypatch.setattr(
        "magiceditor.services.app_log.user_data_dir",
        lambda: fallback_dir,
    )
    dest = setup_logging(blocked)
    assert dest == fallback_dir / "MagicEditor.log"
    assert dest.is_file()
    assert "Logging started" in dest.read_text(encoding="utf-8")
