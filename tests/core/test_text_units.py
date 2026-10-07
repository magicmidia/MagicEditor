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


def _shown(raw: bytes, encoding: str = "utf-8") -> str:
    return raw.decode(encoding, errors="replace")


def _hold_backspace(raw: bytes, encoding: str = "utf-8") -> None:
    """Each backspace must delete bytes. The replacement count must not grow."""
    guard = len(raw) + 2
    while raw:
        shown = _shown(raw, encoding)
        before = shown.count("\ufffd")
        col = len(shown)
        cut = grapheme_start(shown, col)
        start = column_to_byte(raw, cut, encoding)
        end = column_to_byte(raw, col, encoding)
        assert end > start, (raw, cut, col, start, end)
        raw = raw[:start] + raw[end:]
        after = _shown(raw, encoding).count("\ufffd") if raw else 0
        assert after <= before
        assert len(raw) < guard
        guard = len(raw)
    assert raw == b""


def test_truncated_utf8_character_owns_its_whole_span() -> None:
    raw = b"\xf0\x9f\x98X"
    assert _shown(raw) == "\ufffdX"
    assert column_to_byte(raw, 1, "utf-8") == 3
    assert column_to_byte(raw, 2, "utf-8") == 4
    assert byte_to_column(raw, 2, "utf-8") == 0
    assert byte_to_column(raw, 3, "utf-8") == 1
    _hold_backspace(raw)


def test_truncated_euro_is_one_column() -> None:
    raw = b"\xe2\x82"
    assert _shown(raw) == "\ufffd"
    assert column_to_byte(raw, 1, "utf-8") == 2
    _hold_backspace(raw)


def test_cp1252_bytes_as_utf8_have_no_zero_width_column() -> None:
    raw = "ação rápida".encode("cp1252")
    shown = _shown(raw)
    assert shown.count("\ufffd") == 3
    for col in range(1, len(shown) + 1):
        assert column_to_byte(raw, col, "utf-8") == col
        assert column_to_byte(raw, col, "utf-8") > column_to_byte(raw, col - 1, "utf-8")
    _hold_backspace(raw)
    _hold_backspace("Não é uma ação rápida".encode("cp1252"))


def test_backspace_from_middle_of_broken_sequence() -> None:
    raw = b"\xf0\x9f\x98X"
    start = column_to_byte(raw, 0, "utf-8")
    end = column_to_byte(raw, 1, "utf-8")
    assert raw[start:end] == b"\xf0\x9f\x98"
    left = raw[:start] + raw[end:]
    assert left == b"X"
    assert "\ufffd" not in _shown(left)


def test_invalid_columns_stay_monotonic_for_other_codecs() -> None:
    samples = (
        ("utf-8", b"\xc0\x80"),
        ("utf-8", b"\xed\xa0\x80"),
        ("utf-16-le", "ção".encode("utf-16-le") + b"\x61"),
        ("utf-16", b"\xff\xfe\x61\x00\xff" + "b".encode("utf-16-le")),
        ("utf-16", b"\xff\xfe\x61\x00\xff"),
        ("utf-16", b"\xff\xfe\x61"),
        ("gbk", bytes((0x81, 0x30, 0x40))),
        ("shift_jis", "あ".encode("shift_jis") + b"\x80"),
        ("cp1252", b"\x81a"),
        ("utf-32-le", b"\x61\x00\x00"),
    )
    for encoding, raw in samples:
        shown = raw.decode(encoding, errors="replace")
        prev = 0
        for col in range(1, len(shown) + 1):
            off = column_to_byte(raw, col, encoding)
            assert off > prev, (encoding, raw, col, off, prev)
            assert byte_to_column(raw, off, encoding) == col
            prev = off
        assert prev == len(raw)
        _hold_backspace(raw, encoding)


def test_random_utf8_backspace_never_regrows_replacement() -> None:
    import random

    rng = random.Random(0)
    for _ in range(40):
        raw = bytes(rng.randrange(256) for _ in range(rng.randrange(1, 32)))
        shown = _shown(raw)
        prev = 0
        for col in range(1, len(shown) + 1):
            off = column_to_byte(raw, col, "utf-8")
            assert off > prev
            assert byte_to_column(raw, off, "utf-8") == col
            prev = off
        assert prev == len(raw)
        _hold_backspace(raw)
