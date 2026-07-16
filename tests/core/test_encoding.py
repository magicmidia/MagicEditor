"""Encoding/EOL probe tests."""

from __future__ import annotations

from magiceditor.core.encoding import decode_bytes, detect_eol


def test_detect_lf() -> None:
    assert detect_eol(b"a\nb\n") == "LF"


def test_detect_crlf() -> None:
    assert detect_eol(b"a\r\nb\r\n") == "CRLF"


def test_decode_utf8() -> None:
    probe = decode_bytes("ação".encode())
    assert "ação" in probe.text
