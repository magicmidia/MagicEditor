"""Folder search respects is_cancelled on the real search_folder path."""

from __future__ import annotations

from pathlib import Path

from magiceditor.services.folder_search import search_folder


def test_search_folder_cancelled(tmp_path: Path | None = None) -> None:
    # Prefer explicit path under workspace to avoid pytest basetemp permission issues
    root = Path("tests") / "_tmp_search_cancel"
    root.mkdir(parents=True, exist_ok=True)
    try:
        for i in range(5):
            (root / f"f{i}.txt").write_text(f"needle {i}\n", encoding="utf-8")
        hits = search_folder(root, "needle", is_cancelled=lambda: True)
        assert hits is None
        hits2 = search_folder(root, "needle", is_cancelled=lambda: False)
        assert hits2 is not None
        assert len(hits2) >= 1
    finally:
        for p in root.glob("*"):
            p.unlink(missing_ok=True)
        root.rmdir()
