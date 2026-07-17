"""Document model backed by a piece table (optional huge/mmap mode)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from magiceditor.core.encoding import EncodingName, Eol, normalize_newlines
from magiceditor.core.line_index import LineIndex
from magiceditor.core.piece_table import PieceTable


@dataclass
class Document:
    """Editable document backed by a piece table."""

    buffer: PieceTable
    path: Path | None = None
    encoding: EncodingName = "utf-8"
    eol: Eol = "LF"
    modified: bool = False
    title: str = "Untitled"
    # When True, UI uses VirtualEditor (viewport only) instead of QPlainTextEdit.
    huge_mode: bool = False
    # Keep mmap alive while document is open (if used).
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
        raw = self.buffer.get_text()
        return raw.decode(
            self.encoding if self.encoding != "utf-8-sig" else "utf-8", errors="replace"
        )

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
        """Insert bytes and update the line index incrementally when possible."""
        if not data:
            return
        idx = self.line_index()
        line = idx.offset_to_line(min(offset, len(self.buffer)))
        self.buffer.insert(offset, data)
        self.modified = True
        if b"\n" not in data and b"\r" not in data:
            idx.apply_insert_plain(offset, len(data))
        else:
            idx.rebuild_suffix(self.buffer, line)

    def delete_bytes(self, offset: int, length: int) -> None:
        """Delete bytes and update the line index incrementally when possible."""
        if length <= 0:
            return
        idx = self.line_index()
        # Peek deleted region for newlines before mutating
        deleted = self.buffer.get_text(offset, length)
        line = idx.offset_to_line(min(offset, len(self.buffer)))
        self.buffer.delete(offset, length)
        self.modified = True
        if b"\n" not in deleted and b"\r" not in deleted:
            idx.apply_delete_plain(offset, length)
        else:
            idx.rebuild_suffix(self.buffer, line)

    def display_name(self) -> str:
        mark = " *" if self.modified else ""
        return f"{self.title}{mark}"

    def set_encoding(self, encoding: EncodingName) -> None:
        """Change preferred save encoding (does not rewrite buffer bytes)."""
        if encoding == self.encoding:
            return
        self.encoding = encoding
        self.modified = True

    def set_eol(self, eol: Eol) -> None:
        """Set EOL policy. For small buffers, rewrite line endings immediately."""
        if eol in {"MIXED", "NONE"}:
            return
        if eol == self.eol and not self.huge_mode:
            return
        if not self.huge_mode:
            data = normalize_newlines(self.buffer.get_text(), eol)
            # Rebuild piece table with normalized bytes
            text = data.decode(
                self.encoding if self.encoding != "utf-8-sig" else "utf-8",
                errors="replace",
            )
            self.buffer = PieceTable(text)
            self._line_index = None
        self.eol = eol
        self.modified = True

    def close(self) -> None:
        mmap_src = self._mmap
        self._mmap = None
        if mmap_src is not None:
            close = getattr(mmap_src, "close", None)
            if callable(close):
                close()
