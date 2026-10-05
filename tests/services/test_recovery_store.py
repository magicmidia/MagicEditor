"""Crash-recovery sidecar (no Qt)."""

from pathlib import Path

from magiceditor.services.recovery_store import (
    apply_recovery,
    read_recovery,
    session_recovery_payload,
    write_recovery,
)
from magiceditor.services.session_state import SessionState


def test_write_read_roundtrip_and_bad_version(tmp_path: Path) -> None:
    target = tmp_path / "a.txt"
    target.write_text("x", encoding="utf-8")
    state = SessionState(
        open_files=[str(target), str(tmp_path / "missing.txt")],
        active_file=str(target),
        drafts=[{"title": "a.txt", "text": "edited", "path": str(target)}],
        bookmarks={str(target): [1, 1, -3]},
        cursors={str(target): (2, 4)},
    )
    path = tmp_path / "recovery.json"
    write_recovery(path, session_recovery_payload(state))
    payload = read_recovery(path)
    assert payload is not None
    assert payload["version"] == 1
    assert len(payload["open_files"]) == 1
    assert payload["drafts"][0]["text"] == "edited"
    assert payload["drafts"][0]["path"]
    assert not path.with_suffix(path.suffix + ".tmp").exists()

    path.write_text('{"version": 99}', encoding="utf-8")
    assert read_recovery(path) is None
    assert read_recovery(tmp_path / "nope.json") is None


def test_apply_recovery_replaces_lists_even_when_empty() -> None:
    state = SessionState(
        open_files=["C:/kept"],
        drafts=[{"title": "old", "text": "old"}],
        theme="nord",
    )
    loaded = apply_recovery(
        state,
        {"version": 1, "open_files": [], "drafts": [], "bookmarks": {}, "cursors": {}},
    )
    assert loaded.open_files == []
    assert loaded.drafts == []
    assert loaded.theme == "nord"
