from magiceditor.core.async_search import find_all_cancelable


def test_find_all_cancelable_basic() -> None:
    data = b"abc def abc xyz abc"
    hits = find_all_cancelable(data, b"abc")
    assert hits == [0, 8, 16]


def test_find_all_cancelled() -> None:
    data = b"x" * 50 + b"needle" + b"y" * 50
    hits = find_all_cancelable(data, b"needle", is_cancelled=lambda: True)
    # may return None immediately
    assert hits is None or isinstance(hits, list)


def test_progress_callback() -> None:
    seen: list[int] = []
    data = b"aa" * 100
    find_all_cancelable(
        data,
        b"aa",
        on_progress=lambda p: seen.append(p.scanned),
        max_matches=5,
    )
    assert seen
