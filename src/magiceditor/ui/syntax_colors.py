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
    "log_error": ("#FF5370", True),
    "log_warn": ("#FFCB6B", True),
    "log_info": ("#82AAFF", False),
    "log_debug": ("#7F8C9F", False),
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
    "log_error": ("#C62828", True),
    "log_warn": ("#B45309", True),
    "log_info": ("#1565C0", False),
    "log_debug": ("#64748B", False),
}


def palette_for(*, light: bool) -> dict[str, tuple[str, bool]]:
    return LIGHT if light else DARK
