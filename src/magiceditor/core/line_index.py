"""Line start index for byte buffers and piece tables."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from magiceditor.core.piece_table import PieceTable


class LineIndex:
    """Maps line numbers to byte offsets (LF, CR, CRLF).

    A trailing newline creates an empty final line (common editor behavior).
    Supports incremental updates for plain inserts and suffix rebuilds.
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
        """Build index from any buffer supporting ``len`` and int indexing."""
        finder = getattr(data, "find", None)
        if callable(finder) and not isinstance(data, str):
            try:
                return cls._from_find(data)
            except (TypeError, ValueError):
                pass
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
    def _from_find(cls, data: Any) -> LineIndex:
        """Index newlines via ``bytes.find`` (no per-byte Python loop)."""
        n = len(data)
        starts: list[int] = []
        content_ends: list[int] = []
        start = 0
        pos = 0
        while pos < n:
            lf = data.find(b"\n", pos)
            cr = data.find(b"\r", pos)
            if lf < 0 and cr < 0:
                break
            if cr < 0 or (0 <= lf < cr):
                starts.append(start)
                content_ends.append(lf)
                start = lf + 1
                pos = start
            else:
                starts.append(start)
                content_ends.append(cr)
                if cr + 1 < n:
                    nxt = data[cr + 1 : cr + 2]
                    if nxt in (b"\n", 10):
                        start = cr + 2
                        pos = start
                        continue
                start = cr + 1
                pos = start
        starts.append(start)
        content_ends.append(n)
        return cls(starts, content_ends, n)

    @classmethod
    def from_piece_table(cls, table: PieceTable) -> LineIndex:
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

    def apply_insert_plain(self, offset: int, delta: int) -> None:
        """Shift index for an insert that contains **no** CR/LF bytes."""
        if delta == 0:
            return
        if offset < 0 or offset > self._length:
            raise IndexError("insert offset out of range")
        for i in range(len(self._starts)):
            if self._starts[i] > offset:
                self._starts[i] += delta
            if self._content_ends[i] >= offset:
                self._content_ends[i] += delta
        self._length += delta

    def apply_delete_plain(self, offset: int, delta: int) -> None:
        """Shift index for a delete that does not remove any CR/LF bytes."""
        if delta == 0:
            return
        if offset < 0 or delta < 0 or offset + delta > self._length:
            raise IndexError("delete range out of range")
        end = offset + delta
        for i in range(len(self._starts)):
            if self._starts[i] >= end:
                self._starts[i] -= delta
            elif self._starts[i] > offset:
                self._starts[i] = offset
            if self._content_ends[i] >= end:
                self._content_ends[i] -= delta
            elif self._content_ends[i] > offset:
                self._content_ends[i] = offset
        self._length -= delta

    def rebuild_suffix(self, table: PieceTable, from_line: int) -> None:
        """Rebuild line boundaries from ``from_line`` to EOF using table bytes.

        Lines before ``from_line`` are kept. Cost is proportional to the
        suffix size — cheap when editing near the end of a huge file.
        """
        from_line = max(from_line, 0)
        if from_line >= len(self._starts):
            from_line = max(0, len(self._starts) - 1)

        start = self._starts[from_line]
        total = len(table)
        start = min(start, total)
        suffix = table.get_text(start, total - start) if total > start else b""
        sub = LineIndex.from_bytes(suffix)

        head_starts = self._starts[:from_line]
        head_ends = self._content_ends[:from_line]
        self._starts = head_starts + [s + start for s in sub._starts]
        self._content_ends = head_ends + [e + start for e in sub._content_ends]
        self._length = total


def is_byte_sequence(data: Sequence[int]) -> bool:
    return hasattr(data, "__len__") and hasattr(data, "__getitem__")
