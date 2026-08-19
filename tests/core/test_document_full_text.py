import pytest

from magiceditor.core.document import Document
from magiceditor.core.editor_surface import EditorSurface
from magiceditor.core.piece_table import PieceTable


def test_full_text_fail_closed_in_huge_mode() -> None:
    doc = Document(buffer=PieceTable("hello"), huge_mode=True)
    with pytest.raises(ValueError):
        doc.full_text(max_bytes=None)
    assert "hello" in doc.full_text(max_bytes=64)


def test_editor_surface_protocol_on_dummy() -> None:
    class Dummy:
        def goto_line(self, line: int, column: int = 0) -> None:
            self.pos = (line, column)

        def has_selection(self) -> bool:
            return False

        def insert(self, text: str) -> None:
            self.buf = text

    d = Dummy()
    d.insert("x")
    assert isinstance(d, EditorSurface)
    assert d.buf == "x"
