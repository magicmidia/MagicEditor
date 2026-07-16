"""Line start index for byte buffers and piece tables."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from magiceditor.core.piece_table import PieceTable


class LineIndex:
    """Maps line numbers to byte offsets (LF, CR, CRLF).

    A trailing newline creates an empty final line (common editor behavior).
    """

    __slots__ = ("_content_ends", "_length", "_starts")

    def __init__(
        self,
        starts: list[int],
        content_ends: list[int],
        length: int,
    ) -> None:
        if len(starts) != len(content_ends):
            raise ValueError("starts and content_ends length mismatch")
        self._starts = starts
        self._content_ends = content_ends
        self._length = length

    @classmethod
    def from_bytes(cls, data: bytes) -> LineIndex:
        return cls.from_buffer(data)

    @classmethod
    def from_buffer(cls, data: Any) -> LineIndex:
        """Build index from any buffer supporting ``len`` and int indexing.

        Works with ``bytes``, ``bytearray``, ``memoryview``, and mmap views
        without requiring an intermediate full ``bytes`` copy of the file.
        """
        starts: list[int] = []
        content_ends: list[int] = []
        start = 0
        i = 0
        n = len(data)
        while i < n:
            b = data[i]
            if isinstance(b, bytes):
                b = b[0]
            if b == 0x0A:  # LF
                starts.append(start)
                content_ends.append(i)
                start = i + 1
                i += 1
            elif b == 0x0D:  # CR or CRLF
                starts.append(start)
                content_ends.append(i)
                if i + 1 < n:
                    nxt = data[i + 1]
                    if isinstance(nxt, bytes):
                        nxt = nxt[0]
                    if nxt == 0x0A:
                        start = i + 2
                        i += 2
                        continue
                start = i + 1
                i += 1
            else:
                i += 1
        starts.append(start)
        content_ends.append(n)
        return cls(starts, content_ends, n)

    @classmethod
    def from_piece_table(cls, table: PieceTable) -> LineIndex:
        # Prefer buffer scan without materializing when table is a single original piece.
        return cls.from_bytes(table.get_text())

    @property
    def line_count(self) -> int:
        return len(self._starts)

    def line_start(self, line: int) -> int:
        if line < 0 or line >= len(self._starts):
            raise IndexError("line out of range")
        return self._starts[line]

    def line_length(self, line: int) -> int:
        if line < 0 or line >= len(self._starts):
            raise IndexError("line out of range")
        return self._content_ends[line] - self._starts[line]

    def offset_to_line(self, offset: int) -> int:
        if offset < 0 or offset > self._length:
            raise IndexError("offset out of range")
        lo, hi = 0, len(self._starts) - 1
        ans = 0
        while lo <= hi:
            mid = (lo + hi) // 2
            if self._starts[mid] <= offset:
                ans = mid
                lo = mid + 1
            else:
                hi = mid - 1
        return ans


def is_byte_sequence(data: Sequence[int]) -> bool:
    return hasattr(data, "__len__") and hasattr(data, "__getitem__")
