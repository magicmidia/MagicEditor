from magiceditor.core.document import Document
from magiceditor.core.line_edit_range import swap_line_with_neighbor
from magiceditor.core.outline_scan import OUTLINE_MAX_BYTES, extract_outline_from_bytes


def test_swap_line_with_neighbor_only_touches_pair() -> None:
    doc = Document.from_text("a\nb\nc\n")
    assert swap_line_with_neighbor(doc, 1, up=True) == 0
    assert doc.line_text(0).rstrip() == "b"
    assert doc.line_text(1).rstrip() == "a"
    assert doc.line_text(2).rstrip() == "c"


def test_outline_scan_caps_bytes() -> None:
    raw = b"# title\n" + (b"x" * (OUTLINE_MAX_BYTES + 100)) + b"\n# late\n"
    entries = extract_outline_from_bytes(raw)
    titles = [t for _ln, _lv, t in entries]
    assert "title" in titles
    assert "late" not in titles
