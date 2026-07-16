"""Clean print / PDF export — force light printable styles."""

from __future__ import annotations


def printable_css() -> str:
    """CSS applied when exporting/printing (ignore dark theme)."""
    return """
    body { background: #ffffff; color: #000000; font-family: sans-serif; }
    pre, code { background: #ffffff; color: #000000; }
    """
