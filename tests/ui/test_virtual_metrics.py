from magiceditor.ui.virtual_metrics import (
    ensure_visible,
    scroll_origin,
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


class _WrapDoc(_Doc):
    def line_text(self, i: int) -> str:
        return "x"


class _WrapEditor(_Editor):
    """Editor fake com word wrap: ``rows`` = display rows por linha."""

    def __init__(self, rows: list[int], *, height: int = 200, lh: int = 20) -> None:
        super().__init__(lines=len(rows), height=height, lh=lh)
        self._word_wrap = True
        self._rows = rows
        self._doc = _WrapDoc(len(rows))

    def _wrap_display_rows(self, text: str) -> list[tuple[int, int, str]]:
        # ``line_text`` sets ``_call_line`` before this runs.
        n = self._rows[self._call_line]
        return [(i, i + 1, "x") for i in range(max(1, n))]

    _call_line = 0


def _wrapped_update(ed: _WrapEditor) -> None:
    # _wrapped_max_scroll chama line_text(v) e depois _wrap_display_rows(text);
    # o fake precisa saber a linha — intercepte via line_text.
    original = ed._doc.line_text

    def line_text(i: int) -> str:
        ed._call_line = i
        return original(i)

    ed._doc.line_text = line_text  # type: ignore[method-assign]
    update_scrollbars(ed)


def test_wrap_max_scroll_accounts_for_wrapped_tail() -> None:
    # 30 linhas; a última ocupa 4 display rows; 10 slots visíveis.
    ed = _WrapEditor([1] * 29 + [4])
    _wrapped_update(ed)
    # Sem wrap seria 20; a cauda com wrap precisa de 3 posições extras.
    assert ed._vsb.hi == 23


def test_wrap_whole_document_fits() -> None:
    ed = _WrapEditor([1] * 5)
    _wrapped_update(ed)
    assert ed._vsb.hi == 0


def test_wrap_single_giant_line_scrollable_to_it() -> None:
    ed = _WrapEditor([1] * 4 + [40])
    _wrapped_update(ed)
    # Linha gigante (40 rows > 10 slots): rola até a linha (4) e depois
    # dentro dela (sub-row scroll) até a última row: 4 + (40 - 10).
    assert ed._vsb.hi == 34


def test_toggle_wrap_recomputes_range_immediately() -> None:
    ed = _WrapEditor([1] * 29 + [4])
    ed._word_wrap = False
    update_scrollbars(ed)
    assert ed._vsb.hi == 20  # contrato não-wrap: lines - visible
    ed._word_wrap = True
    _wrapped_update(ed)
    assert ed._vsb.hi == 23


def test_scroll_origin_plain_and_wrap() -> None:
    ed = _Editor(lines=30)
    ed._vsb.setValue(7)
    assert scroll_origin(ed) == (7, 0)

    w = _WrapEditor([1] * 4 + [40])
    _wrapped_update(w)
    w._vsb.setValue(2)
    assert scroll_origin(w) == (2, 0)
    # Além de lines-1: rola dentro da última linha (skip rows).
    w._vsb.setValue(7)
    assert scroll_origin(w) == (4, 3)


def test_ensure_visible_scrolls_wrapped_caret_above_footer() -> None:
    """A wrap on the last on-screen line used to paint under the footer.

    10 slots, 10 document lines, the last one occupies 2 display rows and
    the caret sits on the second row. Scroll must move so that row fits.
    """
    ed = _WrapEditor([1] * 9 + [2], height=200, lh=20)
    _wrapped_update(ed)
    ed._cursor_col = 1  # boundary of row 0 lands on the wrapped row
    assert ed._vsb.val == 0
    ensure_visible(ed, 9)
    assert ed._vsb.val == 1


def test_ensure_visible_keeps_wrapped_caret_already_on_screen() -> None:
    ed = _WrapEditor([1] * 9 + [2], height=200, lh=20)
    _wrapped_update(ed)
    ed._cursor_col = 0  # first display row, still inside the viewport
    ensure_visible(ed, 9)
    assert ed._vsb.val == 0


def test_giant_last_line_reachable_to_final_row() -> None:
    ed = _WrapEditor([1] * 4 + [40])
    _wrapped_update(ed)
    visible = visible_line_slots(ed)
    assert ed._vsb.hi == 4 + (40 - visible)
    ed._vsb.setValue(ed._vsb.hi)
    first, skip = scroll_origin(ed)
    assert first == 4
    # No scroll máximo, as rows restantes da última linha cobrem o fundo.
    assert ed._rows[4] - skip >= visible
