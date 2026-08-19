from magiceditor.core.multi_cursor import (
    find_all_in_line_source,
    find_all_occurrences,
    find_next_in_line_source,
    find_next_occurrence,
    restore_carets_after_multi_insert,
    word_at,
)


def test_find_next_and_all() -> None:
    lines = ["aa bb aa", "xx aa yy"]
    nxt = find_next_occurrence(lines, "aa", after_line=0, after_col=1)
    assert nxt is not None
    assert nxt.line == 0 and nxt.col == 6
    all_hits = find_all_occurrences(lines, "aa")
    assert len(all_hits) == 3


def test_find_next_in_line_source_does_not_preload() -> None:
    """K14: accessor is called per line, never handed a full list."""
    store = {0: "aa xx", 1: "yy aa"}
    seen: list[int] = []

    def line_at(i: int) -> str:
        seen.append(i)
        return store[i]

    hit = find_next_in_line_source(line_at, 2, "aa", after_line=0, after_col=1)
    assert hit is not None
    assert hit.line == 1 and hit.col == 3
    assert seen[0] == 0
    all_hits = find_all_in_line_source(line_at, 2, "aa", max_hits=200)
    assert len(all_hits) == 2


def test_ctrl_d_paths_do_not_call_full_read_lines() -> None:
    from pathlib import Path

    src = Path("src/magiceditor/ui/power_features.py").read_text(encoding="utf-8")
    add = src.split("def multi_cursor_add_next", 1)[1].split("def multi_cursor_select_all", 1)[0]
    all_fn = src.split("def multi_cursor_select_all", 1)[1].split("def multi_cursor_clear", 1)[0]
    assert "read_lines(tab.document)" not in add
    assert "read_lines(tab.document)" not in all_fn
    assert "find_next_in_line_source" in add
    assert "find_all_in_line_source" in all_fn


def test_word_at() -> None:
    lines = ["hello_world"]
    w = word_at(lines, 0, 3)
    assert w is not None
    assert w[0] == "hello_world"


def test_restore_carets_one() -> None:
    primary, extras = restore_carets_after_multi_insert([(2, 5)])
    assert primary == (2, 5)
    assert extras == []


def test_restore_carets_three_invariant() -> None:
    # Input order is reverse-apply (bottom-up) — function must not drop any
    carets = [(2, 2), (1, 2), (0, 2)]
    primary, extras = restore_carets_after_multi_insert(carets)
    all_pos = {primary, *[(a, b) for a, b, c in extras]}
    assert primary == (2, 2)  # bottommost
    assert len(all_pos) == 3
    assert all_pos == {(0, 2), (1, 2), (2, 2)}
    assert len(extras) + 1 == 3
    # extras must not include primary
    assert all((a, b) != primary for a, b, _c in extras)


def test_restore_carets_dedupe() -> None:
    primary, extras = restore_carets_after_multi_insert([(0, 1), (0, 1), (1, 1)])
    all_pos = {primary, *[(a, b) for a, b, _ in extras]}
    assert len(all_pos) == 2
    assert primary == (1, 1)
