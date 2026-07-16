"""mmap policy tests."""

from __future__ import annotations

from magiceditor.core.mmap_source import MMAP_THRESHOLD_BYTES, should_use_mmap


def test_small_files_stay_in_memory() -> None:
    assert should_use_mmap("x.bin", size_bytes=MMAP_THRESHOLD_BYTES) is False
    assert should_use_mmap("x.bin", size_bytes=1024) is False


def test_large_files_use_mmap() -> None:
    assert should_use_mmap("x.bin", size_bytes=MMAP_THRESHOLD_BYTES + 1) is True
