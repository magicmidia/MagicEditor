"""Newline edits match a full rescan and must not copy the suffix each time."""

from __future__ import annotations

import os
import time

from magiceditor.core.line_index import LineIndex
from magiceditor.core.piece_table import PieceTable
from magiceditor.services.document import Document

_SAMPLES = (
    b"",
    b"a",
    b"ab",
    b"a\nb",
    b"a\rb",
    b"a\r\nb",
    b"a\r\n",
    b"\n",
    b"\r\n",
    b"a\nb\nc",
    b"a\r\nb\nc\r",
    b"\ra\n",
    b"ab\ncd",
    b"aa\nbb\ncc",
    b"hello\nworld",
)
_INSERTS = (b"\n", b"\r", b"\r\n", b"X\nY", b"\n\n", b"\r\r", b"X")


def _doc(raw: bytes) -> Document:
    return Document(buffer=PieceTable(raw), encoding="utf-8", eol="LF", title="t")


def _matches_rescan(doc: Document) -> None:
    raw = doc.buffer.get_text(0, len(doc.buffer))
    fresh = LineIndex.from_bytes(raw)
    idx = doc.line_index()
    assert idx.line_count == fresh.line_count, raw
    assert idx._length == len(raw)
    for line in range(fresh.line_count):
        assert idx.line_start(line) == fresh.line_start(line), (raw, line)
        assert idx.line_length(line) == fresh.line_length(line), (raw, line)
        start = fresh.line_start(line)
        length = fresh.line_length(line)
        assert doc.buffer.get_text(start, length) == raw[start : start + length]


def test_newline_edits_match_full_rescan() -> None:
    for sample in _SAMPLES:
        for offset in range(len(sample) + 1):
            for payload in _INSERTS:
                doc = _doc(sample)
                same = doc.line_index()
                doc.insert_bytes(offset, payload)
                assert doc.line_index() is same
                _matches_rescan(doc)
        for start in range(len(sample)):
            for length in range(1, len(sample) - start + 1):
                doc = _doc(sample)
                doc.delete_bytes(start, length)
                _matches_rescan(doc)


def _index_budget(seconds: float) -> float:
    if os.environ.get("GITHUB_ACTIONS"):
        return 2.0
    return seconds


def test_near_start_newline_beats_suffix_copy() -> None:
    # A full suffix copy of this buffer misses the CI budget (2s) even on a
    # machine about twice as fast as the one that measured ~0.6 ms/MB.
    size = 32 * 1024 * 1024
    reps = 240
    doc = _doc(b"a" * size)
    doc.line_index()
    started = time.perf_counter()
    for _ in range(reps):
        doc.insert_bytes(1, b"\n")
    elapsed = time.perf_counter() - started
    limit = _index_budget(0.35)
    assert elapsed < limit, f"newline edits took {elapsed:.3f}s, budget {limit:.2f}s"
    _matches_rescan(doc)
    raw = doc.buffer.get_text(0, len(doc.buffer))
    assert raw.startswith(b"a" + b"\n" * reps)
    assert doc.line_index().line_count == reps + 1
