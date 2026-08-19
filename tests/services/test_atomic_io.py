from pathlib import Path

from magiceditor.services.atomic_io import write_bytes_atomic, write_chunks_atomic


def test_write_bytes_atomic_replaces(tmp_path: Path) -> None:
    dest = tmp_path / "note.txt"
    dest.write_bytes(b"old")
    write_bytes_atomic(dest, b"new-data")
    assert dest.read_bytes() == b"new-data"
    assert not list(tmp_path.glob(".me-*.tmp"))


def test_write_chunks_atomic_joins(tmp_path: Path) -> None:
    dest = tmp_path / "big.bin"
    write_chunks_atomic(dest, [b"aa", b"bb", b"cc"])
    assert dest.read_bytes() == b"aabbcc"
