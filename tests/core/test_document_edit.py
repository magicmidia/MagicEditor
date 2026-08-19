from magiceditor.core.document_edit import (
    read_lines,
    replace_line_range,
    transform_all_lines,
    transform_line_range,
)
from magiceditor.core.line_ops import sort_lines
from magiceditor.core.piece_table import PieceTable
from magiceditor.services.document import Document


def test_replace_and_transform_lines() -> None:
    doc = Document.from_text("c\nb\na\n")
    lines = read_lines(doc)
    assert lines[:3] == ["c", "b", "a"]
    transform_line_range(doc, 0, 3, sort_lines)
    assert read_lines(doc)[:3] == ["a", "b", "c"]


def test_transform_all_lines_preserves_trailing_newline() -> None:
    """Whole-file sort of ``c\\nb\\na\\n`` must stay ``a\\nb\\nc\\n``, not ``\\na\\nb\\nc``."""
    doc = Document.from_text("c\nb\na\n")
    assert transform_all_lines(doc, sort_lines) is True
    assert doc.text() == "a\nb\nc\n"


def test_transform_all_lines_huge_keeps_uncapped_bytes() -> None:
    raw = b"c\nb\na\n"
    doc = Document(buffer=PieceTable(raw), huge_mode=True)
    assert transform_all_lines(doc, sort_lines) is True
    assert doc.buffer.get_text(0, len(doc.buffer)) == b"a\nb\nc\n"


def test_replace_middle_range() -> None:
    doc = Document.from_text("one\ntwo\nthree\n")
    replace_line_range(doc, 1, 2, ["TWO"])
    text = doc.text()
    assert "TWO" in text
    assert "one" in text
