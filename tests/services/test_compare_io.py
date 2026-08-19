from pathlib import Path

from magiceditor.services.compare_io import COMPARE_CAP_BYTES, read_compare_text
from magiceditor.services.quick_open_scan import iter_workspace_files


def test_read_compare_text_caps(tmp_path: Path) -> None:
    p = tmp_path / "big.txt"
    p.write_bytes(b"a" * (COMPARE_CAP_BYTES + 50))
    text = read_compare_text(p)
    assert len(text.encode("utf-8")) <= COMPARE_CAP_BYTES


def test_quick_open_scan_skips_git(tmp_path: Path) -> None:
    (tmp_path / "keep.py").write_text("x", encoding="utf-8")
    git = tmp_path / ".git"
    git.mkdir()
    (git / "HEAD").write_text("ref", encoding="utf-8")
    files = iter_workspace_files(tmp_path)
    assert any(p.endswith("keep.py") for p in files)
    assert not any(".git" in p.replace("\\", "/") for p in files)
