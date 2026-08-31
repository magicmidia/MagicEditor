"""Line start index for byte buffers and piece tables."""

from __future__ import annotations

import array
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
        starts: Sequence[int],
        content_ends: Sequence[int],
        length: int,
    ) -> None:
        if len(starts) != len(content_ends):
            raise ValueError("starts and content_ends length mismatch")
        if isinstance(starts, array.array) and starts.typecode == "q":
            self._starts = starts
        else:
            self._starts = array.array("q", starts)
        if isinstance(content_ends, array.array) and content_ends.typecode == "q":
            self._content_ends = content_ends
        else:
            self._content_ends = array.array("q", content_ends)
        self._length = length

    @classmethod
    def from_bytes(cls, data: bytes) -> LineIndex:
        return cls.from_buffer(data)

    @classmethod
    def from_buffer(cls, data: Any) -> LineIndex:
        """Build index from any buffer supporting ``len`` and int indexing."""
        # Unpack memoryview to its underlying object (e.g. mmap, bytes) for C-speed find
        obj = getattr(data, "obj", None) if isinstance(data, memoryview) else None
        if obj is not None and hasattr(obj, "find"):
            data = obj
        finder = getattr(data, "find", None)
        if callable(finder) and not isinstance(data, str):
            try:
                return cls._from_find(data)
            except (TypeError, ValueError):
                pass
        starts = array.array("q")
        content_ends = array.array("q")
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
        """Index newlines via ``data.find`` in strict O(N) linear time.

        ``bytes``/``mmap`` ``find`` is memchr-speed in C; benchmarks showed it
        beats a chunked ``re.finditer`` scan (Match-object allocation per line
        costs more than the Python loop here).
        """
        n = len(data)
        starts = array.array("q")
        content_ends = array.array("q")
        starts.append(0)

        if n == 0:
            content_ends.append(0)
            return cls(starts, content_ends, 0)

        has_cr = data.find(b"\r") != -1
        has_lf = data.find(b"\n") != -1

        if not has_cr and not has_lf:
            content_ends.append(n)
            return cls(starts, content_ends, n)

        if not has_cr:
            # Fast path for pure LF files (Unix / SQL / Logs / Source code)
            find = data.find
            nl = b"\n"
            append_start = starts.append
            append_end = content_ends.append
            pos = 0
            while pos < n:
                lf = find(nl, pos)
                if lf < 0:
                    break
                append_end(lf)
                pos = lf + 1
                if pos < n:
                    append_start(pos)
                else:
                    append_start(n)
                    append_end(n)
                    return cls(starts, content_ends, n)
            append_end(n)
            return cls(starts, content_ends, n)

        # Path with CR / CRLF / Mixed newlines
        pos = 0
        next_lf = data.find(b"\n", 0)
        next_cr = data.find(b"\r", 0)

        while pos < n:
            if next_lf < pos and next_lf != -1:
                next_lf = data.find(b"\n", pos)
            if next_cr < pos and next_cr != -1:
                next_cr = data.find(b"\r", pos)

            if next_lf < 0 and next_cr < 0:
                break

            if next_cr < 0 or (0 <= next_lf < next_cr):
                content_ends.append(next_lf)
                pos = next_lf + 1
            else:
                content_ends.append(next_cr)
                if next_cr + 1 < n and data[next_cr + 1 : next_cr + 2] in (b"\n", 10):
                    pos = next_cr + 2
                else:
                    pos = next_cr + 1

            if pos < n:
                starts.append(pos)
            else:
                starts.append(n)
                content_ends.append(n)
                return cls(starts, content_ends, n)

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
        new_starts = array.array("q", head_starts)
        new_starts.extend(s + start for s in sub._starts)
        new_ends = array.array("q", head_ends)
        new_ends.extend(e + start for e in sub._content_ends)
        self._starts = new_starts
        self._content_ends = new_ends
        self._length = total


def is_byte_sequence(data: Sequence[int]) -> bool:
    return hasattr(data, "__len__") and hasattr(data, "__getitem__")
