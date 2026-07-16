"""Syntax highlighting helpers (pure Python)."""

from magiceditor.core.syntax.detect import (
    detect_language,
    language_label,
    supported_languages,
)
from magiceditor.core.syntax.rules import rules_for, tokenize_line

__all__ = [
    "detect_language",
    "language_label",
    "rules_for",
    "supported_languages",
    "tokenize_line",
]
