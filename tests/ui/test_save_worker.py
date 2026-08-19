"""K15: SaveWorker writes via document_io on a background thread."""

from __future__ import annotations

from pathlib import Path

import pytest

from magiceditor.core.document import Document
from magiceditor.ui.save_worker import SaveWorker, begin_document_save


@pytest.mark.ui
def test_save_worker_writes_document_bytes(qapp, tmp_path: Path) -> None:
    dest = tmp_path / "k15.txt"
    dest.write_text("old", encoding="utf-8")
    doc = Document.from_text("chunk-k15")
    doc.path = dest
    worker = SaveWorker(doc, dest)
    worker.start()
    assert worker.wait(8000)
    assert dest.read_text(encoding="utf-8") == "chunk-k15"
    assert doc.modified is False


@pytest.mark.ui
def test_begin_document_save_emits_succeeded(qapp, qtbot, tmp_path: Path) -> None:
    dest = tmp_path / "ok.txt"
    dest.write_text("x", encoding="utf-8")
    doc = Document.from_text("via-helper")
    seen: list[str] = []
    worker = begin_document_save(qapp, doc, dest, seen.append, lambda _m: None)
    qtbot.waitUntil(lambda: bool(seen), timeout=8000)
    assert worker.isFinished()
    assert Path(seen[0]).name == "ok.txt"
    assert dest.read_text(encoding="utf-8") == "via-helper"


def test_save_current_uses_worker_not_sync_save() -> None:
    from magiceditor.ui import main_window as mw

    src = Path(mw.__file__).read_text(encoding="utf-8")
    assert "begin_document_save" in src
    assert "save_document(tab.document)" not in src
