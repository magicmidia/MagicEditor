"""Folder scope: a walk must not read a target outside the opened folder."""

import os
import stat
from pathlib import Path

from magiceditor.services.document_io import open_document
from magiceditor.services.folder_search import search_folder
from magiceditor.services.fs_scope import stays_inside
from magiceditor.services.quick_open_scan import iter_workspace_files
from magiceditor.ui.window_files import same_open_path


def test_stays_inside_accepts_file_and_rejects_sibling(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    inside = root / "note.txt"
    inside.write_text("local", encoding="utf-8")
    outside = tmp_path / "secret.txt"
    outside.write_text("secret", encoding="utf-8")
    assert stays_inside(inside, root) is True
    assert stays_inside(outside, root) is False


def _as_symlink(monkeypatch, link: Path, target: Path) -> None:
    """Pretend ``link`` is a symlink. ``os.lstat`` does not open the target."""
    link_key = os.path.normcase(os.path.abspath(link))
    real_lstat = os.lstat
    real_readlink = os.readlink

    def lstat(path, *args, **kwargs):
        key = os.path.normcase(os.path.abspath(path))
        if key == link_key:
            return os.stat_result((stat.S_IFLNK | 0o777, 0, 0, 1, 0, 0, 0, 0, 0, 0))
        return real_lstat(path, *args, **kwargs)

    def readlink(path, *args, **kwargs):
        key = os.path.normcase(os.path.abspath(path))
        if key == link_key:
            return str(target)
        return real_readlink(path, *args, **kwargs)

    monkeypatch.setattr(os, "lstat", lstat)
    monkeypatch.setattr(os, "readlink", readlink)


def test_search_and_quick_open_skip_symlink_outside_the_folder(tmp_path: Path, monkeypatch) -> None:
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    secret = outside_dir / "secret.txt"
    secret.write_text("needle-secret\n", encoding="utf-8")
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "local.txt").write_text("needle-local\n", encoding="utf-8")
    link = root / "alias.txt"
    link.write_text("needle-secret\n", encoding="utf-8")
    _as_symlink(monkeypatch, link, secret)

    hits = search_folder(root, "needle")
    assert {hit.path.name for hit in hits} == {"local.txt"}
    assert all("secret" not in hit.text for hit in hits)

    names = {Path(path).name for path in iter_workspace_files(root)}
    assert "local.txt" in names
    assert "alias.txt" not in names


def test_open_document_refuses_directory_without_a_content_read(
    tmp_path: Path, monkeypatch
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    note = root / "note.txt"
    note.write_bytes(b"hello")
    calls = {"n": 0}
    real_read = Path.read_bytes

    def read_bytes(self: Path, *args, **kwargs):
        calls["n"] += 1
        return real_read(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    try:
        open_document(root)
    except OSError:
        pass
    else:
        raise AssertionError("a directory must be refused")
    assert calls["n"] == 0

    doc = open_document(note)
    assert doc.buffer.get_text() == b"hello"
    assert calls["n"] == 1


def test_same_open_path_refuses_directory_without_resolve(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    note = root / "note.txt"
    note.write_text("x", encoding="utf-8")

    def boom(self: Path, *args, **kwargs):
        raise AssertionError("resolve")

    monkeypatch.setattr(Path, "resolve", boom)
    assert same_open_path(root, root) is False
    assert same_open_path(note, note) is True
    assert same_open_path(note, root / "other.txt") is False
