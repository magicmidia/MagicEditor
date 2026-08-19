"""Outline scan with a byte cap (K7)."""

from __future__ import annotations

import re

_MD_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
OUTLINE_MAX_BYTES = 2 * 1024 * 1024


def extract_markdown_outline(text: str) -> list[tuple[int, int, str]]:
    out: list[tuple[int, int, str]] = []
    for i, line in enumerate(text.splitlines(), start=1):
        m = _MD_HEADING.match(line)
        if m:
            out.append((i, len(m.group(1)), m.group(2).strip()))
    return out


def extract_outline_from_bytes(
    raw: bytes, *, max_bytes: int = OUTLINE_MAX_BYTES
) -> list[tuple[int, int, str]]:
    chunk = raw[:max_bytes]
    text = chunk.decode("utf-8", errors="replace")
    return extract_markdown_outline(text)
