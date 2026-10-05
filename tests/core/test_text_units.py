"""Raw-byte column mapping must not expand U+FFFD."""

from __future__ import annotations

from magiceditor.core.text_units import (
    byte_to_column,
    column_to_byte,
    grapheme_end,
    grapheme_start,
)


def test_column_roundtrip_utf8() -> None:
    raw = "ação".encode()
    assert column_to_byte(raw, 2, "utf-8") == len("aç".encode())
    assert byte_to_column(raw, column_to_byte(raw, 2, "utf-8"), "utf-8") == 2
    assert column_to_byte(raw, 99, "utf-8") == len(raw)


def test_invalid_byte_is_one_column_not_three() -> None:
    raw = b"ab\xc3cd"
    # decode(replace) is "ab�cd" (5 chars). The bad byte must stay 1 byte wide.
    assert column_to_byte(raw, 3, "utf-8") == 3
    assert column_to_byte(raw, 4, "utf-8") == 4
    assert column_to_byte(raw, len(raw.decode("utf-8", "replace")), "utf-8") == len(raw)


def test_backspace_widths_shrink_invalid_line() -> None:
    raw = b"ab\xc3cd"
    col = len(raw.decode("utf-8", "replace"))
    while col:
        cut = grapheme_start(raw.decode("utf-8", "replace"), col)
        start = column_to_byte(raw, cut, "utf-8")
        end = column_to_byte(raw, col, "utf-8")
        assert end > start
        raw = raw[:start] + raw[end:]
        col = len(raw.decode("utf-8", "replace"))
    assert raw == b""


def test_grapheme_eats_combining_mark() -> None:
    text = "cafe\u0301"
    assert grapheme_start(text, len(text)) == 3
    assert grapheme_end(text, 3) == len(text)
    assert grapheme_start("ção", 3) == 2
