"""Code-point boundaries on raw encoded bytes.

Editing must not round-trip through ``errors='replace'``. That turns one
invalid byte into U+FFFD (3 UTF-8 bytes) and the next backspace eats into
the following character, which is what leaves a trail of ``�``.
"""

from __future__ import annotations

import codecs
import unicodedata

_UTF8 = frozenset({"utf-8", "utf-8-sig"})


def codec_name(encoding: str) -> str:
    return encoding if encoding != "utf-8-sig" else "utf-8"


def column_to_byte(raw: bytes, col: int, encoding: str) -> int:
    """Byte length of the first ``col`` decoded characters of ``raw``."""
    if col <= 0 or not raw:
        return 0
    enc = codec_name(encoding)
    try:
        text = raw.decode(enc)
    except UnicodeDecodeError:
        ends = _char_ends(raw, enc)
        if col >= len(ends):
            return len(raw)
        return ends[col - 1]
    if col >= len(text):
        return len(raw)
    return len(text[:col].encode(enc))


def byte_to_column(raw: bytes, byte_off: int, encoding: str) -> int:
    """Character column at ``byte_off`` (snaps back to a character edge)."""
    if byte_off <= 0 or not raw:
        return 0
    byte_off = min(len(raw), byte_off)
    enc = codec_name(encoding)
    try:
        return len(raw[:byte_off].decode(enc))
    except UnicodeDecodeError:
        col = 0
        for end in _char_ends(raw, enc):
            if end > byte_off:
                break
            col += 1
        return col


def grapheme_start(text: str, col: int) -> int:
    """Column of the grapheme that ends at ``col`` (combining marks, ZWJ, VS)."""
    if col <= 0:
        return 0
    i = min(col, len(text)) - 1
    while i > 0 and _extends_previous(text[i]):
        i -= 1
    while i > 0 and text[i - 1] == "\u200d":
        i -= 1
        while i > 0 and _extends_previous(text[i]):
            i -= 1
    return i


def grapheme_end(text: str, col: int) -> int:
    """Column just after the grapheme that starts at ``col``."""
    n = len(text)
    if col >= n:
        return n
    i = col + 1
    while i < n and (_extends_previous(text[i]) or text[i - 1] == "\u200d"):
        i += 1
    return i


def _extends_previous(ch: str) -> bool:
    if unicodedata.combining(ch):
        return True
    code = ord(ch)
    if code in (0xFE0E, 0xFE0F, 0x200D):
        return True
    return 0x1F3FB <= code <= 0x1F3FF


_span_stack: list[list[tuple[int, int]]] = []


def _record_replace(exc: UnicodeDecodeError) -> tuple[str, int]:
    """Same resume point as ``errors='replace'``, recording each bad span."""
    end = exc.end
    if end <= exc.start:
        end = exc.start + 1
    obj = exc.object
    if isinstance(obj, (bytes, bytearray)) and end > len(obj):
        end = len(obj)
    if _span_stack:
        _span_stack[-1].append((exc.start, end))
    return ("\ufffd", end)


codecs.register_error("magiceditor.replace", _record_replace)


def _char_ends(raw: bytes, encoding: str) -> list[int]:
    """Byte offset after each ``decode(errors='replace')`` character.

    One U+FFFD owns the whole span the codec rejects. Columns stay strictly
    increasing, so backspace always deletes at least one byte.
    """
    spans: list[tuple[int, int]] = []
    _span_stack.append(spans)
    try:
        raw.decode(encoding, errors="magiceditor.replace")
    finally:
        _span_stack.pop()
    ends: list[int] = []
    cursor = 0
    size = len(raw)
    for start, bad_end in spans:
        if start > cursor:
            _append_strict_ends(ends, raw[cursor:start], encoding, cursor)
        span_end = bad_end if bad_end > cursor else cursor + 1
        span_end = min(span_end, size)
        _push_end(ends, span_end, size)
        cursor = max(cursor + 1, span_end)
    if cursor < size:
        _append_strict_ends(ends, raw[cursor:], encoding, cursor)
    return ends


def _append_strict_ends(ends: list[int], chunk: bytes, encoding: str, base: int) -> None:
    dec = codecs.getincrementaldecoder(encoding)("strict")
    limit = base + len(chunk)
    for index in range(len(chunk)):
        out = dec.decode(chunk[index : index + 1])
        if out:
            _push_chars(ends, len(out), base + index + 1, limit)
    tail = dec.decode(b"", final=True)
    if tail:
        _push_chars(ends, len(tail), limit, limit)


def _push_end(ends: list[int], end: int, limit: int) -> None:
    prev = ends[-1] if ends else 0
    if end <= prev or end > limit:
        return
    ends.append(end)


def _push_chars(ends: list[int], nchars: int, end: int, limit: int) -> None:
    if nchars <= 1:
        _push_end(ends, end, limit)
        return
    prev = ends[-1] if ends else 0
    if end - prev >= nchars:
        for step in range(1, nchars):
            ends.append(prev + step)
    _push_end(ends, end, limit)
