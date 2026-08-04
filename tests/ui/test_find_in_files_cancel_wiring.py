"""FindInFilesDialog passes cancel hook into search_folder."""

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


def test_run_search_forwards_is_cancelled(qapp) -> None:
    cancelled = {"v": False}

    def is_cancelled() -> bool:
        return cancelled["v"]

    root = Path("tests") / "_tmp_fif"
    root.mkdir(parents=True, exist_ok=True)
    (root / "a.txt").write_text("hello world\n", encoding="utf-8")
    try:
        dlg = FindInFilesDialog(
            root,
            is_cancelled=is_cancelled,
            on_cancel_request=lambda: cancelled.__setitem__("v", True),
            on_search_start=lambda: cancelled.__setitem__("v", False),
        )
        dlg.find_input.setText("hello")
        idx = dlg.scope_box.findData("workspace")
        dlg.scope_box.setCurrentIndex(max(0, idx))

        with patch(
            "magiceditor.ui.find_in_files_dialog.search_folder",
            return_value=[],
        ) as mocked:
            dlg.run_search()
            assert mocked.called
            kwargs = mocked.call_args.kwargs
            assert "is_cancelled" in kwargs
            assert kwargs["is_cancelled"] is is_cancelled
    finally:
        for p in root.glob("*"):
            p.unlink(missing_ok=True)
        root.rmdir()
