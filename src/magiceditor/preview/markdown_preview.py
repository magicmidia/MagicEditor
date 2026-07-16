"""Markdown/HTML preview controller (WebEngine integration later)."""

from __future__ import annotations

import markdown as md


def render_markdown(source: str) -> str:
    """Convert Markdown source to HTML string."""
    return md.markdown(source, extensions=["fenced_code", "tables"])
