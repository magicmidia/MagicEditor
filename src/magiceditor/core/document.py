"""Document model backed by a piece table (optional huge/mmap mode)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from magiceditor.core.encoding import EncodingName, Eol, normalize_newlines
from magiceditor.core.line_index import LineIndex
from magiceditor.core.line_index_splice import note_delete, note_insert
from magiceditor.core.piece_table import PieceTable
from magiceditor.core.syntax_limits import FULL_TEXT_MAX_BYTES

# Re-export so callers need not import services
__all__ = ["Document"]


@dataclass
class Document:
    """Editable document backed by a piece table."""

    buffer: PieceTable
    path: Path | None = None
    encoding: EncodingName = "utf-8"
    eol: Eol = "LF"
    modified: bool = False
    title: str = "Untitled"
    huge_mode: bool = False
    syntax_enabled: bool = True
    _mmap: Any = field(default=None, repr=False, compare=False)
    _line_index: LineIndex | None = field(default=None, repr=False, compare=False)

    @classmethod
    def blank(cls, title: str = "Untitled") -> Document:
        return cls(buffer=PieceTable(), title=title)

    @classmethod
    def from_text(
        cls,
        text: str,
        *,
        path: Path | None = None,
        encoding: EncodingName = "utf-8",
        eol: Eol = "LF",
    ) -> Document:
        title = path.name if path is not None else "Untitled"
        return cls(
            buffer=PieceTable(text),
            path=path,
            encoding=encoding,
            eol=eol,
            modified=False,
            title=title,
            huge_mode=False,
        )

    def mark_modified(self) -> None:
        self.modified = True

    def invalidate_line_index(self) -> None:
        self._line_index = None

    def text(self) -> str:
        if self.huge_mode:
            return self.full_text(max_bytes=FULL_TEXT_MAX_BYTES)
        return self.full_text(max_bytes=None)

    def full_text(self, *, max_bytes: int | None = FULL_TEXT_MAX_BYTES) -> str:
        """Decode buffer text. Fail-closed: huge_mode requires an explicit cap."""
        if self.huge_mode and max_bytes is None:
            raise ValueError("full_text requires max_bytes in huge_mode")
        limit = len(self.buffer) if max_bytes is None else min(len(self.buffer), max_bytes)
        raw = self.buffer.get_text(0, limit)
        enc = self.encoding if self.encoding != "utf-8-sig" else "utf-8"
        text = raw.decode(enc, errors="replace")
        if max_bytes is not None and len(self.buffer) > max_bytes:
            text += "\n\n… [truncated]"
        return text

    def line_index(self) -> LineIndex:
        if self._line_index is None:
            self._line_index = LineIndex.from_piece_table(self.buffer)
        return self._line_index

    def line_text(self, line: int) -> str:
        idx = self.line_index()
        start = idx.line_start(line)
        length = idx.line_length(line)
        raw = self.buffer.get_text(start, length)
        enc = self.encoding if self.encoding != "utf-8-sig" else "utf-8"
        return raw.decode(enc, errors="replace")

    def insert_bytes(self, offset: int, data: bytes) -> None:
        if not data:
            return
        idx = self.line_index()
        self.buffer.insert(offset, data)
        self.modified = True
        note_insert(idx, self.buffer, offset, data)

    def delete_bytes(self, offset: int, length: int) -> None:
        if length <= 0:
            return
        idx = self.line_index()
        deleted = self.buffer.get_text(offset, length)
        self.buffer.delete(offset, length)
        self.modified = True
        note_delete(idx, self.buffer, offset, deleted)

    def display_name(self) -> str:
        mark = " *" if self.modified else ""
        return f"{self.title}{mark}"

    def set_encoding(self, encoding: EncodingName) -> None:
        if encoding == self.encoding:
            return
        self.encoding = encoding
        self.modified = True

    def set_eol(self, eol: Eol) -> None:
        if eol in {"MIXED", "NONE"}:
            return
        if eol == self.eol and not self.huge_mode:
            return
        if not self.huge_mode:
            data = normalize_newlines(self.buffer.get_text(), eol)
            text = data.decode(
                self.encoding if self.encoding != "utf-8-sig" else "utf-8",
                errors="replace",
            )
            self.buffer = PieceTable(text)
            self._line_index = None
        self.eol = eol
        self.modified = True

    def close(self) -> None:
        if hasattr(self.buffer, "release") and callable(self.buffer.release):
            self.buffer.release()
        mmap_src = self._mmap
        self._mmap = None
        if mmap_src is not None:
            close = getattr(mmap_src, "close", None)
            if callable(close):
                close()
