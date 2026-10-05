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


def _char_ends(raw: bytes, encoding: str) -> list[int]:
    """Byte offset after each character, matching ``decode(errors='replace')``."""
    dec = codecs.getincrementaldecoder(encoding)("replace")
    ends: list[int] = []
    start = 0
    for i in range(len(raw)):
        out = dec.decode(raw[i : i + 1])
        if not out:
            continue
        _append_ends(ends, start, i + 1, len(out))
        start = i + 1
    tail = dec.decode(b"", final=True)
    if tail:
        _append_ends(ends, start, len(raw), len(tail))
    return ends


def _append_ends(ends: list[int], start: int, pos: int, nchars: int) -> None:
    span = pos - start
    if nchars <= 0:
        return
    if nchars == 1:
        ends.append(pos)
        return
    if span == nchars:
        ends.extend(range(start + 1, pos + 1))
        return
    if span <= 0:
        ends.extend([pos] * nchars)
        return
    if span >= nchars:
        base, rem = divmod(span, nchars)
        acc = start
        for k in range(nchars):
            acc += base + (1 if k < rem else 0)
            ends.append(acc)
        return
    ends.extend([start] * (nchars - 1))
    ends.append(pos)
