"""Encoding catalog breadth."""

from __future__ import annotations

from magiceditor.core.encoding import ENCODING_CATALOG, decode_bytes, encode_text


def test_catalog_size() -> None:
    assert len(ENCODING_CATALOG) >= 50


def test_roundtrip_utf8() -> None:
    raw = encode_text("olá 世界", "utf-8")
    probe = decode_bytes(raw)
    assert "olá" in probe.text


def test_roundtrip_cp1252() -> None:
    raw = "café".encode("cp1252")
    probe = decode_bytes(raw)
    assert "café" in probe.text


def test_bom_utf8() -> None:
    raw = b"\xef\xbb\xbfhello"
    probe = decode_bytes(raw)
    assert probe.encoding == "utf-8-sig"
    assert probe.text.startswith("hello")
