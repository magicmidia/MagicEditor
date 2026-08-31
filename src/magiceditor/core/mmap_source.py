"""Memory-mapped file source for large documents."""

from __future__ import annotations

import mmap
from pathlib import Path
from types import TracebackType

# Architecture: files larger than this use mmap instead of full RAM read.
MMAP_THRESHOLD_BYTES = 5 * 1024 * 1024


def should_use_mmap(path: Path | str, size_bytes: int | None = None) -> bool:
    """Return True when the file should be opened via mmap."""
    if size_bytes is None:
        size_bytes = Path(path).stat().st_size
    return size_bytes > MMAP_THRESHOLD_BYTES


class MmapSource:
    """Read-only mmap view; supports len() and slice -> bytes."""

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)
        self._file = self._path.open("rb")
        try:
            self._mmap = mmap.mmap(self._file.fileno(), 0, access=mmap.ACCESS_READ)
        except ValueError:
            # Empty file: mmap may fail on some platforms
            self._mmap = None

    def __len__(self) -> int:
        if self._mmap is None:
            return 0
        return len(self._mmap)

    def __getitem__(self, key: slice | int) -> bytes:
        if self._mmap is None:
            if isinstance(key, int):
                raise IndexError("empty mmap")
            return b""
        data = self._mmap[key]
        if isinstance(data, int):
            return bytes([data])
        return bytes(data)

    def read_all(self) -> bytes:
        return self[:]

    def as_memoryview(self) -> memoryview:
        """Zero-copy view of the mapped file (empty if file is empty)."""
        if self._mmap is None:
            return memoryview(b"")
        return memoryview(self._mmap)

    def close(self) -> None:
        if self._mmap is not None:
            try:
                self._mmap.close()
            except BufferError:
                pass
            self._mmap = None
        if hasattr(self, "_file") and not self._file.closed:
            self._file.close()

    def __enter__(self) -> MmapSource:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()
