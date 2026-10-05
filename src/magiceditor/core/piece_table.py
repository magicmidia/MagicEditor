"""Piece table text buffer for efficient edits without full string rebuilds."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SourceKind = Literal["original", "add"]


@dataclass(slots=True)
class Piece:
    """A span into either the original source or the add-buffer."""

    source: SourceKind
    offset: int
    length: int


class PieceTable:
    """Logical document as an ordered list of pieces.

    Query ranges for the viewport; do not materialize huge documents as one str.
    Offsets and lengths are in **bytes** (UTF-8 logical buffer).
    """

    def __init__(self, original: bytes | str | memoryview = "") -> None:
        # ``memoryview`` (e.g. from mmap) is kept by reference — no full RAM copy.
        if isinstance(original, str):
            self._original: bytes | memoryview = original.encode("utf-8")
        else:
            self._original = original
        self._add = bytearray()
        self._pieces: list[Piece] = []
        if len(self._original):
            self._pieces.append(Piece(source="original", offset=0, length=len(self._original)))
        self._length = len(self._original)

    def __len__(self) -> int:
        return self._length

    def get_text(self, start: int = 0, length: int | None = None) -> bytes:
        """Return a slice of the logical document as bytes."""
        total = self._length
        if length is None:
            length = total - start
        if start < 0 or length < 0 or start + length > total:
            raise IndexError("slice out of range")
        if length == 0:
            return b""

        out = bytearray()
        remaining_skip = start
        remaining_take = length
        for piece in self._pieces:
            if remaining_take <= 0:
                break
            if remaining_skip >= piece.length:
                remaining_skip -= piece.length
                continue
            local_start = remaining_skip
            take = min(piece.length - local_start, remaining_take)
            out.extend(self._read_piece(piece, local_start, take))
            remaining_skip = 0
            remaining_take -= take
        return bytes(out)

    def release(self) -> None:
        """Release underlying memoryview if holding one."""
        if isinstance(self._original, memoryview):
            try:
                self._original.release()
            except (BufferError, ValueError):
                pass
            self._original = b""

    def iter_chunks(self, size: int = 256 * 1024):
        """Yield buffer slices sequentially without quadratic piece seeking."""
        if size <= 0:
            raise ValueError("chunk size must be positive")
        buf = bytearray()
        for piece in self._pieces:
            src = self._original if piece.source == "original" else self._add
            p_off = piece.offset
            p_len = piece.length
            while p_len > 0:
                take = min(p_len, size - len(buf))
                chunk = src[p_off : p_off + take]
                buf.extend(chunk)
                p_off += take
                p_len -= take
                if len(buf) >= size:
                    yield bytes(buf)
                    buf.clear()
        if buf:
            yield bytes(buf)

    def insert(self, offset: int, data: bytes | str) -> None:
        """Insert bytes (or UTF-8 string) at logical offset."""
        if isinstance(data, str):
            data = data.encode("utf-8")
        if not data:
            return
        if offset < 0 or offset > self._length:
            raise IndexError("insert offset out of range")

        add_offset = len(self._add)
        self._add.extend(data)
        new_piece = Piece(source="add", offset=add_offset, length=len(data))

        if offset == self._length:
            self._pieces.append(new_piece)
            self._length += len(data)
            # Typed text is contiguous in the add-buffer. Merge the tail once
            # so a long edit does not leave one piece per keystroke.
            self._coalesce_tail()
            return
        if offset == 0:
            self._pieces.insert(0, new_piece)
            self._length += len(data)
            self._coalesce_around(0)
            return

        index, local = self._locate(offset)
        piece = self._pieces[index]
        if local == 0:
            self._pieces.insert(index, new_piece)
            at = index
        elif local == piece.length:
            self._pieces.insert(index + 1, new_piece)
            at = index + 1
        else:
            left = Piece(source=piece.source, offset=piece.offset, length=local)
            right = Piece(
                source=piece.source,
                offset=piece.offset + local,
                length=piece.length - local,
            )
            self._pieces[index : index + 1] = [left, new_piece, right]
            at = index + 1
        self._length += len(data)
        self._coalesce_around(at)

    def delete(self, offset: int, length: int) -> None:
        """Delete ``length`` bytes starting at logical offset."""
        if length == 0:
            return
        if offset < 0 or length < 0 or offset + length > self._length:
            raise IndexError("delete range out of range")
        if self._delete_inside_one_piece(offset, length):
            return

        end = offset + length
        new_pieces: list[Piece] = []
        cursor = 0
        for piece in self._pieces:
            piece_start = cursor
            piece_end = cursor + piece.length
            cursor = piece_end

            if piece_end <= offset or piece_start >= end:
                new_pieces.append(piece)
                continue

            # Overlap: keep head and/or tail outside [offset, end).
            if piece_start < offset:
                keep = offset - piece_start
                new_pieces.append(Piece(source=piece.source, offset=piece.offset, length=keep))
            if piece_end > end:
                local_start = max(0, end - piece_start)
                new_pieces.append(
                    Piece(
                        source=piece.source,
                        offset=piece.offset + local_start,
                        length=piece_end - end,
                    )
                )

        self._pieces = [p for p in new_pieces if p.length > 0]
        self._length -= length
        self._coalesce_all()

    def _locate(self, offset: int) -> tuple[int, int]:
        """Return (piece_index, local_offset) for a logical offset in [0, length)."""
        remaining = offset
        for i, piece in enumerate(self._pieces):
            if remaining < piece.length:
                return i, remaining
            remaining -= piece.length
        raise IndexError("offset out of range")

    def _read_piece(self, piece: Piece, local_start: int, take: int) -> bytes:
        start = piece.offset + local_start
        end = start + take
        if piece.source == "original":
            chunk = self._original[start:end]
            return chunk if isinstance(chunk, bytes) else bytes(chunk)
        return bytes(self._add[start:end])

    def _delete_inside_one_piece(self, offset: int, length: int) -> bool:
        """Shrink one piece. False when the range crosses a piece boundary."""
        if not self._pieces:
            return False
        last = self._pieces[-1]
        last_start = self._length - last.length
        if last_start <= offset:
            self._shrink_piece(len(self._pieces) - 1, offset - last_start, length)
            return True
        index, local = self._locate(offset)
        if local + length <= self._pieces[index].length:
            self._shrink_piece(index, local, length)
            return True
        return False

    def _shrink_piece(self, index: int, local: int, length: int) -> None:
        piece = self._pieces[index]
        if length >= piece.length:
            del self._pieces[index]
        elif local == 0:
            self._pieces[index] = Piece(piece.source, piece.offset + length, piece.length - length)
        elif local + length == piece.length:
            self._pieces[index] = Piece(piece.source, piece.offset, local)
        else:
            left = Piece(piece.source, piece.offset, local)
            right = Piece(
                piece.source,
                piece.offset + local + length,
                piece.length - local - length,
            )
            self._pieces[index : index + 1] = [left, right]
        self._length -= length

    def _coalesce_around(self, index: int) -> None:
        """Merge the new piece with its neighbors. Does not walk the whole table."""
        if len(self._pieces) < 2:
            return
        i = max(0, index - 1)
        limit = min(len(self._pieces) - 1, max(index, 0) + 1)
        while i < len(self._pieces) - 1 and i <= limit:
            prev = self._pieces[i]
            nxt = self._pieces[i + 1]
            if prev.source == nxt.source and prev.offset + prev.length == nxt.offset:
                self._pieces[i] = Piece(prev.source, prev.offset, prev.length + nxt.length)
                del self._pieces[i + 1]
                limit = min(limit, len(self._pieces) - 1)
            else:
                i += 1

    def _coalesce_tail(self) -> None:
        """Collapse a run of contiguous pieces at the end of the table."""
        i = len(self._pieces) - 1
        while i > 0:
            prev = self._pieces[i - 1]
            nxt = self._pieces[i]
            if prev.source == nxt.source and prev.offset + prev.length == nxt.offset:
                self._pieces[i - 1] = Piece(prev.source, prev.offset, prev.length + nxt.length)
                del self._pieces[i]
                i -= 1
            else:
                break

    def _coalesce_all(self) -> None:
        if len(self._pieces) < 2:
            return
        merged: list[Piece] = [self._pieces[0]]
        for piece in self._pieces[1:]:
            prev = merged[-1]
            if prev.source == piece.source and prev.offset + prev.length == piece.offset:
                merged[-1] = Piece(
                    source=prev.source,
                    offset=prev.offset,
                    length=prev.length + piece.length,
                )
            else:
                merged.append(piece)
        self._pieces = merged
