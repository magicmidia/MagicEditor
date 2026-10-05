"""Auto-close brackets. Pure: no Qt, so tests stay headless."""

from __future__ import annotations

_PAIRS = {"(": ")", "[": "]", "{": "}", '"': '"', "'": "'"}
_CLOSERS = {")", "]", "}"}


def bracket_insert(ch: str, selection: str, next_ch: str) -> tuple[str, int] | None:
    """Return ``(inserted, caret_back)``.

    ``caret_back == -1`` means jump over an existing closer (insert nothing,
    column + 1). Otherwise the caller inserts ``inserted`` and moves the caret
    back by ``caret_back`` characters so it sits before the closer.
    """
    if len(ch) != 1:
        return None
    if not selection and ch in _CLOSERS and next_ch == ch:
        return ("", -1)
    if not selection and ch in {'"', "'"} and next_ch == ch:
        return ("", -1)
    closer = _PAIRS.get(ch)
    if closer is None:
        return None
    body = selection if selection else ""
    return (ch + body + closer, len(closer))
