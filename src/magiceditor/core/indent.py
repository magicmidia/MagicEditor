"""Indent helpers (pure — no Qt)."""

from __future__ import annotations


def indent_unit(*, spaces: bool, width: int) -> str:
    n = max(2, min(8, int(width)))
    return (" " * n) if spaces else "\t"


def leading_whitespace(line: str) -> str:
    i = 0
    while i < len(line) and line[i] in " \t":
        i += 1
    return line[:i]


def extra_indent_after(line: str, language: str, unit: str) -> str:
    """Return extra indent when the line opens a block."""
    stripped = line.rstrip()
    if not stripped:
        return ""
    if language == "python" and stripped.endswith(":"):
        return unit
    if stripped.endswith(("{", "[", "(")):
        return unit
    return ""


def newline_auto_indent(line_before_cursor: str, language: str, unit: str) -> str:
    """Text to insert after a newline (leading ws + optional extra indent)."""
    ws = leading_whitespace(line_before_cursor)
    return ws + extra_indent_after(line_before_cursor, language, unit)


def unindent_prefix(line: str, width: int) -> int:
    """How many leading characters to strip for one unindent step."""
    n = max(2, min(8, int(width)))
    if line.startswith("\t"):
        return 1
    if line.startswith(" " * n):
        return n
    if line.startswith(" "):
        return min(n, len(line) - len(line.lstrip(" ")))
    return 0
