"""Line index from buffer / memoryview."""

from __future__ import annotations

from magiceditor.core.line_index import LineIndex


def test_from_buffer_memoryview() -> None:
    data = memoryview(b"a\nb\nc")
    idx = LineIndex.from_buffer(data)
    assert idx.line_count == 3
    assert idx.line_start(1) == 2


def test_from_buffer_matches_bytes() -> None:
    raw = b"one\r\ntwo\r\n"
    a = LineIndex.from_bytes(raw)
    b = LineIndex.from_buffer(memoryview(raw))
    assert a.line_count == b.line_count
    assert a.line_start(0) == b.line_start(0)
    assert a.line_start(1) == b.line_start(1)
