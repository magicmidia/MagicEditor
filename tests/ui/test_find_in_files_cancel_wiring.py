"""FindInFilesDialog runs folder search on a worker with cancel wiring (K5)."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

pytest.importorskip("PyQt6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from magiceditor.ui.find_in_files_dialog import FindInFilesDialog


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_run_search_starts_worker_with_cancel_hook(qapp) -> None:
    root = Path("tests") / "_tmp_fif"
    root.mkdir(parents=True, exist_ok=True)
    (root / "a.txt").write_text("hello world\n", encoding="utf-8")
    try:
        dlg = FindInFilesDialog(root)
        dlg.find_input.setText("hello")
        idx = dlg.scope_box.findData("workspace")
        dlg.scope_box.setCurrentIndex(max(0, idx))

        with patch(
            "magiceditor.ui.find_in_files_worker.search_folder",
            return_value=[],
        ) as mocked:
            dlg.run_search()
            worker = dlg._worker
            assert worker is not None
            worker.wait(5000)
            assert mocked.called
            kwargs = mocked.call_args.kwargs
            assert "is_cancelled" in kwargs
            is_cancelled = kwargs["is_cancelled"]
            assert is_cancelled() is False
            dlg._request_cancel()
            assert is_cancelled() is True
    finally:
        for p in root.glob("*"):
            p.unlink(missing_ok=True)
        root.rmdir()
