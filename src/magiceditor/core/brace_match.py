"""Matching brace / bracket finder for a single string (visible range safe)."""

from __future__ import annotations

PAIRS = {
    "(": ")",
    "[": "]",
    "{": "}",
    "<": ">",
}
CLOSING = {v: k for k, v in PAIRS.items()}


def find_matching_brace(text: str, pos: int) -> int | None:
    """Return index of matching brace for character at ``pos``, or None.

    ``pos`` is a character index into ``text``. Scans only within ``text``
    (callers should pass the visible buffer slice or a bounded window).
    """
    if pos < 0 or pos >= len(text):
        return None
    ch = text[pos]
    if ch in PAIRS:
        open_ch, close_ch = ch, PAIRS[ch]
        depth = 0
        for i in range(pos, len(text)):
            c = text[i]
            if c == open_ch:
                depth += 1
            elif c == close_ch:
                depth -= 1
                if depth == 0:
                    return i
        return None
    if ch in CLOSING:
        open_ch, close_ch = CLOSING[ch], ch
        depth = 0
        for i in range(pos, -1, -1):
            c = text[i]
            if c == close_ch:
                depth += 1
            elif c == open_ch:
                depth -= 1
                if depth == 0:
                    return i
        return None
    return None


def brace_at_or_near(text: str, pos: int) -> int | None:
    """If ``pos`` is on a brace return it; else try pos-1 (cursor after brace)."""
    if 0 <= pos < len(text) and (text[pos] in PAIRS or text[pos] in CLOSING):
        return pos
    if pos > 0 and pos - 1 < len(text):
        prev = text[pos - 1]
        if prev in PAIRS or prev in CLOSING:
            return pos - 1
    return None
