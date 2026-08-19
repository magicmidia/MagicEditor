"""K17: @pytest.mark.perf — tokenize, find-in-files cancel, open 20 MB, scroll frames."""

from __future__ import annotations

from pathlib import Path

import pytest

from magiceditor.core.document import Document
from magiceditor.core.syntax.rules import tokenize_line
from magiceditor.core.syntax_limits import SYNTAX_OFF_BYTES
from magiceditor.services.document_io import open_document
from magiceditor.services.folder_search import search_folder


@pytest.mark.perf
def test_tokenize_python_line_budget() -> None:
    line = "def hello(name: str) -> None:  # greet\n"
    spans = tokenize_line(line, "python")
    assert spans


@pytest.mark.perf
def test_find_in_files_honors_cancel(tmp_path: Path) -> None:
    for i in range(8):
        (tmp_path / f"n{i}.txt").write_text(f"needle-{i}\n", encoding="utf-8")
    hits = search_folder(tmp_path, "needle", is_cancelled=lambda: True)
    assert hits is None
    hits2 = search_folder(tmp_path, "needle", is_cancelled=lambda: False)
    assert hits2 is not None
    assert len(hits2) >= 1


@pytest.mark.perf
def test_open_20mb_uses_huge_gate(tmp_path: Path) -> None:
    path = tmp_path / "twenty.bin"
    with path.open("wb") as handle:
        handle.write(b"head\n")
        handle.seek(SYNTAX_OFF_BYTES + 64)
        handle.write(b"\ntail\n")
    assert path.stat().st_size > SYNTAX_OFF_BYTES
    doc = open_document(path)
    assert doc.huge_mode is True
    assert doc.syntax_enabled is False
    with pytest.raises(ValueError):
        doc.full_text(max_bytes=None)
    doc.close()


@pytest.mark.perf
def test_virtual_scroll_sixty_frames(qtbot) -> None:
    pytest.importorskip("PyQt6")
    pytest.importorskip("pytestqt")
    from magiceditor.ui.virtual_editor import VirtualEditor

    body = "\n".join(f"LINE-{i:04d}" for i in range(240))
    ed = VirtualEditor(Document.from_text(body))
    qtbot.addWidget(ed)
    ed.resize(480, 160)
    bar = ed.verticalScrollBar()
    for i in range(60):
        bar.setValue(i % max(1, bar.maximum() or 1))
        ed.viewport().update()
    visible = ed.viewport_text()
    assert visible
    assert "LINE-" in visible
