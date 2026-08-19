"""Shared syntax token colors for highlighter + virtual viewport."""

from __future__ import annotations

# kind -> (fg hex, bold)
DARK: dict[str, tuple[str, bool]] = {
    "keyword": ("#C792EA", True),
    "string": ("#C3E88D", False),
    "comment": ("#546E7A", False),
    "number": ("#F78C6C", False),
    "decorator": ("#82AAFF", False),
    "heading": ("#82AAFF", True),
    "code": ("#89DDFF", False),
    "link": ("#80CBC4", False),
}

LIGHT: dict[str, tuple[str, bool]] = {
    "keyword": ("#7C3AED", True),
    "string": ("#15803D", False),
    "comment": ("#64748B", False),
    "number": ("#C2410C", False),
    "decorator": ("#2563EB", False),
    "heading": ("#1D4ED8", True),
    "code": ("#0E7490", False),
    "link": ("#0F766E", False),
}


def palette_for(*, light: bool) -> dict[str, tuple[str, bool]]:
    return LIGHT if light else DARK
