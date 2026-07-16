"""Piece table text buffer (stub — implement with TDD)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Piece:
    """A span into either the original source or the add-buffer."""

    source: str  # "original" | "add"
    offset: int
    length: int


class PieceTable:
    """Logical document as an ordered list of pieces.

    Do not store the full edited document as a single contiguous string
    for huge files; query ranges for the viewport instead.
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

    def __len__(self) -> int:
        return sum(p.length for p in self._pieces)

    def get_text(self, start: int = 0, length: int | None = None) -> bytes:
        """Return a slice of the logical document as bytes."""
        total = len(self)
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

    def _read_piece(self, piece: Piece, local_start: int, take: int) -> bytes:
        start = piece.offset + local_start
        end = start + take
        if piece.source == "original":
            return self._original[start:end]
        return bytes(self._add[start:end])
