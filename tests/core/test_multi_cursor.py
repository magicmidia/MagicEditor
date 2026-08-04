from magiceditor.core.multi_cursor import (
    find_all_occurrences,
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
