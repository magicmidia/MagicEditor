"""Pure text transformations applied to a selection or line.

All functions take and return plain ``str``; scope resolution (selection vs.
current line) is the caller's concern. Unicode-aware (accents preserved).
"""

from __future__ import annotations

import base64
import re
import urllib.parse

_WORD_SPLIT = re.compile(r"(\s+)")
_SENTENCE_SPLIT = re.compile(r"([.!?]+\s+)")


def to_upper(text: str) -> str:
    """Uppercase all cased characters (accent-aware)."""
    return text.upper()


def to_lower(text: str) -> str:
    """Lowercase all cased characters (accent-aware)."""
    return text.lower()


def to_title_case(text: str) -> str:
    """Title Case each whitespace-separated word, preserving accents.

    Uses word-wise ``str.capitalize`` so apostrophes stay intact
    ("don't" -> "Don't", unlike naive ``str.title``).
    """
    parts = _WORD_SPLIT.split(text)
    return "".join(part if i % 2 else part.capitalize() for i, part in enumerate(parts))


def to_sentence_case(text: str) -> str:
    """Uppercase the first letter of each sentence; lowercase the rest.

    Sentences split after ``.``/``!``/``?`` followed by whitespace.
    """
    lowered = text.lower()
    parts = _SENTENCE_SPLIT.split(lowered)
    return "".join(part if i % 2 else _uppercase_first_alpha(part) for i, part in enumerate(parts))


def invert_case(text: str) -> str:
    """Swap upper <-> lower for every cased character."""
    return text.swapcase()


def base64_encode(text: str) -> str:
    """Encode UTF-8 text to an ASCII base64 string."""
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def base64_decode(text: str) -> str:
    """Decode a base64 string back to UTF-8 text.

    Raises:
        ValueError: if the input is not valid base64 or not valid UTF-8.
    """
    try:
        raw = base64.b64decode(text.encode("ascii"), validate=True)
    except (ValueError, UnicodeEncodeError) as exc:
        raise ValueError(f"Invalid base64 input: {exc}") from exc
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"Invalid base64 input: decoded bytes are not UTF-8 ({exc})") from exc


def url_encode(text: str) -> str:
    """Percent-encode text (UTF-8); every reserved character is escaped."""
    return urllib.parse.quote(text, safe="")


def url_decode(text: str) -> str:
    """Percent-decode text; ``+`` is treated as a space."""
    return urllib.parse.unquote_plus(text)


def _uppercase_first_alpha(segment: str) -> str:
    for i, ch in enumerate(segment):
        if ch.isalpha():
            return segment[:i] + ch.upper() + segment[i + 1 :]
    return segment
