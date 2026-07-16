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

    def __init__(self, original: bytes | str = "") -> None:
        if isinstance(original, str):
            self._original = original.encode("utf-8")
        else:
            self._original = original
        self._add = bytearray()
        self._pieces: list[Piece] = []
        if self._original:
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
            return
        if offset == 0:
            self._pieces.insert(0, new_piece)
            self._length += len(data)
            return

        index, local = self._locate(offset)
        piece = self._pieces[index]
        if local == 0:
            self._pieces.insert(index, new_piece)
        elif local == piece.length:
            self._pieces.insert(index + 1, new_piece)
        else:
            left = Piece(source=piece.source, offset=piece.offset, length=local)
            right = Piece(
                source=piece.source,
                offset=piece.offset + local,
                length=piece.length - local,
            )
            self._pieces[index : index + 1] = [left, new_piece, right]
        self._length += len(data)
        self._coalesce_around(index)

    def delete(self, offset: int, length: int) -> None:
        """Delete ``length`` bytes starting at logical offset."""
        if length == 0:
            return
        if offset < 0 or length < 0 or offset + length > self._length:
            raise IndexError("delete range out of range")

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
            return self._original[start:end]
        return bytes(self._add[start:end])

    def _coalesce_around(self, index: int) -> None:
        """Merge adjacent pieces that share source and are contiguous."""
        self._coalesce_all()

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
