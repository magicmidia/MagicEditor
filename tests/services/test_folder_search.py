"""Folder search service tests."""

from __future__ import annotations

from pathlib import Path

from magiceditor.services.folder_search import search_folder


def test_search_finds_literal(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("def hello():\n    return 1\n", encoding="utf-8")
    (tmp_path / "b.txt").write_text("no match here\n", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "c.md").write_text("# hello world\n", encoding="utf-8")

    hits = search_folder(tmp_path, "hello")
    paths = {h.path.name for h in hits}
    assert "a.py" in paths
    assert "c.md" in paths
    assert "b.txt" not in paths


def test_search_case_sensitive(tmp_path: Path) -> None:
    (tmp_path / "x.txt").write_text("Hello HELLO hello\n", encoding="utf-8")
    assert len(search_folder(tmp_path, "hello", case_sensitive=True)) == 1
    assert len(search_folder(tmp_path, "hello", case_sensitive=False)) == 1
    # case-insensitive finds first occurrence only per line
    hits = search_folder(tmp_path, "HELLO", case_sensitive=True)
    assert len(hits) == 1
    assert hits[0].column == 7


def test_search_skips_binaries(tmp_path: Path) -> None:
    (tmp_path / "ok.txt").write_text("needle\n", encoding="utf-8")
    (tmp_path / "pic.png").write_bytes(b"\x89PNG\r\nneedle")
    hits = search_folder(tmp_path, "needle")
    assert len(hits) == 1
    assert hits[0].path.name == "ok.txt"


def test_search_empty_needle(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    assert search_folder(tmp_path, "") == []


def test_search_regex(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("id=42\nid=7\nplain\n", encoding="utf-8")
    hits = search_folder(tmp_path, r"id=\d+", use_regex=True)
    assert len(hits) == 2
    assert hits[0].column == 1


def test_search_texts_open_tabs() -> None:
    from magiceditor.services.folder_search import search_texts

    sources = [
        ("tab:0", "Untitled-1", "alpha beta\n"),
        ("tab:1", "notes.md", "beta gamma\n"),
    ]
    hits = search_texts(sources, "beta")
    assert len(hits) == 2
    assert {h.source_key for h in hits} == {"tab:0", "tab:1"}
