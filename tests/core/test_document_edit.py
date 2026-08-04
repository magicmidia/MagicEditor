from magiceditor.core.document_edit import read_lines, replace_line_range, transform_line_range
from magiceditor.core.line_ops import sort_lines
from magiceditor.services.document import Document


def test_replace_and_transform_lines() -> None:
    doc = Document.from_text("c\nb\na\n")
    lines = read_lines(doc)
    assert lines[:3] == ["c", "b", "a"]
    transform_line_range(doc, 0, 3, sort_lines)
    assert read_lines(doc)[:3] == ["a", "b", "c"]


def test_replace_middle_range() -> None:
    doc = Document.from_text("one\ntwo\nthree\n")
    replace_line_range(doc, 1, 2, ["TWO"])
    text = doc.text()
    assert "TWO" in text
    assert "one" in text
