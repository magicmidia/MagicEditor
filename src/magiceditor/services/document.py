"""In-memory document model (path, buffer, metadata)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from magiceditor.core.encoding import EncodingName, Eol
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
        )

    def mark_modified(self) -> None:
        self.modified = True
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

    def display_name(self) -> str:
        mark = " *" if self.modified else ""
        return f"{self.title}{mark}"
