from magiceditor.ui.virtual_metrics import (
    ensure_visible,
    update_scrollbars,
    usable_line_slots,
    visible_line_slots,
)


class _Bar:
    def __init__(self) -> None:
        self.lo = 0
        self.hi = 0
        self.page = 0
        self.val = 0

    def setRange(self, lo: int, hi: int) -> None:
        self.lo, self.hi = lo, hi

    def setPageStep(self, page: int) -> None:
        self.page = page

    def value(self) -> int:
        return self.val

    def setValue(self, val: int) -> None:
        self.val = val


class _View:
    def __init__(self, width: int, height: int) -> None:
        self._w = width
        self._h = height

    def width(self) -> int:
        return self._w

    def height(self) -> int:
        return self._h


class _Index:
    def __init__(self, n: int) -> None:
        self.line_count = n


class _Doc:
    def __init__(self, n: int) -> None:
        self._n = n

    def line_index(self) -> _Index:
        return _Index(self._n)


class _Editor:
    def __init__(self, *, lines: int = 30, height: int = 200, lh: int = 20) -> None:
        self._line_height = lh
        self._word_wrap = False
        self._show_line_numbers = False
        self._gutter_width = 0
        self._pad_x = 8
        self._doc = _Doc(lines)
        self._vp = _View(400, height)
        self._vsb = _Bar()
        self._hsb = _Bar()

    def viewport(self) -> _View:
        return self._vp

    def verticalScrollBar(self) -> _Bar:
        return self._vsb

    def horizontalScrollBar(self) -> _Bar:
        return self._hsb


def test_visible_and_usable_slots() -> None:
    ed = _Editor(height=200, lh=20)
    assert visible_line_slots(ed) == 10
    assert usable_line_slots(ed) == 10


def test_scrollbar_range_is_flush_with_footer() -> None:
    ed = _Editor(lines=30, height=200, lh=20)
    update_scrollbars(ed)
    # 30 lines, 10 visible → last line sits on the last row (no empty pad)
    assert ed._vsb.hi == 20


def test_ensure_visible_last_line_flush_at_bottom() -> None:
    ed = _Editor(lines=30, height=200, lh=20)
    update_scrollbars(ed)
    ensure_visible(ed, 29)
    assert ed._vsb.val == 20
    assert (29 - ed._vsb.val) == visible_line_slots(ed) - 1
