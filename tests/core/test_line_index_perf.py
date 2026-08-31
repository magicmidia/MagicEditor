"""Performance and scaling tests for LineIndex."""

from __future__ import annotations

import array
import time

from magiceditor.core.line_index import LineIndex


def test_line_index_uses_compact_arrays() -> None:
    data = b"line1\nline2\nline3\n"
    idx = LineIndex.from_bytes(data)
    assert isinstance(idx._starts, array.array)
    assert isinstance(idx._content_ends, array.array)
    assert idx._starts.typecode == "q"
    assert idx._content_ends.typecode == "q"


def test_line_index_30mb_lf_performance() -> None:
    # 30MB of SQL/log-like LF data
    line = b"INSERT INTO `users` (`id`, `name`) VALUES (1, 'Test User');\n"
    count = (30 * 1024 * 1024) // len(line)
    data = line * count

    t0 = time.perf_counter()
    idx = LineIndex.from_bytes(data)
    elapsed = time.perf_counter() - t0

    assert idx.line_count == count + 1
    # Must complete in under 200ms (typically ~35ms)
    assert elapsed < 0.2, f"Line indexing took {elapsed:.4f}s, expected < 0.2s"


def test_line_index_30mb_crlf_performance() -> None:
    # 30MB of CRLF data
    line = b"INSERT INTO `users` (`id`, `name`) VALUES (1, 'Test User');\r\n"
    count = (30 * 1024 * 1024) // len(line)
    data = line * count

    t0 = time.perf_counter()
    idx = LineIndex.from_bytes(data)
    elapsed = time.perf_counter() - t0

    assert idx.line_count == count + 1
    # Must complete in under 250ms (typically ~70ms)
    assert elapsed < 0.25, f"Line indexing took {elapsed:.4f}s, expected < 0.25s"


def test_line_index_from_memoryview() -> None:
    line = b"SELECT * FROM items WHERE id = 42;\n"
    data = memoryview(line * 1000)
    idx = LineIndex.from_buffer(data)
    assert idx.line_count == 1001
    assert idx.line_start(0) == 0
    assert idx.line_start(1) == len(line)
