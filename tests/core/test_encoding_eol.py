"""EOL conversion helpers."""

from __future__ import annotations

from magiceditor.core.encoding import normalize_newlines


def test_normalize_to_lf() -> None:
    assert normalize_newlines(b"a\r\nb\rc\n", "LF") == b"a\nb\nc\n"


def test_normalize_to_crlf() -> None:
    assert normalize_newlines(b"a\nb\n", "CRLF") == b"a\r\nb\r\n"


def test_normalize_to_cr() -> None:
    assert normalize_newlines(b"a\r\nb\n", "CR") == b"a\rb\r"
