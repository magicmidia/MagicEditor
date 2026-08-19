"""J2.7: theme JSON I/O lives in services, not ui."""

from __future__ import annotations

import json
from pathlib import Path

import magiceditor.ui as ui_pkg
from magiceditor.services.theme_io import (
    load_imported_theme,
    read_theme_bundle,
    write_theme_bundle,
)


def test_write_and_read_theme_bundle_roundtrip(tmp_path: Path) -> None:
    dest = tmp_path / "nord.json"
    written = write_theme_bundle(dest, "nord", "qlementine")
    assert written == dest
    data = read_theme_bundle(dest)
    assert data["theme"] == "nord"
    assert data["icon_pack"] == "qlementine"
    assert load_imported_theme(dest) == "nord"
    on_disk = json.loads(dest.read_text(encoding="utf-8"))
    assert on_disk == data


def test_load_imported_theme_rejects_non_object(tmp_path: Path) -> None:
    dest = tmp_path / "bad.json"
    dest.write_text("[1, 2]", encoding="utf-8")
    try:
        read_theme_bundle(dest)
    except ValueError as exc:
        assert "object" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_workspace_actions_has_no_path_read_text() -> None:
    src = (Path(ui_pkg.__file__).resolve().parent / "workspace_actions.py").read_text(
        encoding="utf-8"
    )
    assert "read_text" not in src
    assert "write_text" not in src
    assert "json.loads" not in src
