"""J1.3: line-ops / brace helpers used by the mixin."""

from magiceditor.core.document import Document
from magiceditor.core.line_ops import sort_lines
from magiceditor.ui.line_ops_actions import (
    apply_line_transform,
    comment_transform,
    matching_brace_target,
    move_line,
    tab_width_transform,
)
from magiceditor.ui.nav_palette import goto_anything_file_list, palette_entries_from_actions


class _Sel:
    def __init__(self, a: int, b: int) -> None:
        self._a = a
        self._b = b

    def has_selection(self) -> bool:
        return self._a != self._b

    def _normalized_selection(self) -> tuple[int, int, int, int]:
        return self._a, 0, self._b, 0


def test_matching_brace_target_same_line() -> None:
    lines = ["foo(bar)"]
    assert matching_brace_target(lines, 0, 3, 0) == (0, 7)


def test_apply_line_transform_huge_without_selection_is_capped() -> None:
    """K14: whole-file sort on huge_mode must not require a full-file str."""
    from magiceditor.core.piece_table import PieceTable

    raw = b"c\nb\na\n"
    doc = Document(buffer=PieceTable(raw), huge_mode=True)

    class _NoSel:
        def has_selection(self) -> bool:
            return False

    apply_line_transform(doc, _NoSel(), sort_lines)
    out = doc.buffer.get_text(0, len(doc.buffer))
    assert out == b"a\nb\nc\n"


def test_apply_line_transform_selection_and_move() -> None:
    doc = Document.from_text("b\na\n")
    apply_line_transform(doc, _Sel(0, 1), sort_lines)
    assert doc.text() == "a\nb\n"
    doc2 = Document.from_text("one\ntwo\n")
    assert move_line(doc2, 1, up=True) == 0
    assert doc2.text().startswith("two\n")


def test_comment_and_tab_transforms() -> None:
    fn = comment_transform("python")
    assert fn(["x"])[0].startswith("#")
    to_spaces = tab_width_transform(False, 4)
    assert to_spaces(["\tx"]) == ["    x"]


class _Act:
    def __init__(self, text: str, shortcut: str = "") -> None:
        self._text = text
        self._sc = shortcut

    def text(self) -> str:
        return self._text

    def shortcut(self):
        class _S:
            def __init__(self, s: str) -> None:
                self._s = s

            def toString(self) -> str:
                return self._s

        return _S(self._sc) if self._sc else None


def test_palette_and_goto_file_list() -> None:
    entries = palette_entries_from_actions({"action.save": _Act("&Save", "Ctrl+S")})
    assert entries == [("action.save", "Save", "Ctrl+S")]
    files = goto_anything_file_list(["a.txt", "b.txt"], ["b.txt", "c.txt"])
    assert files == ["a.txt", "b.txt", "c.txt"]
