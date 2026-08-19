"""Deprecated classic QPlainTextEdit path (J2.2 / M6).

The shipped editor surface is ``VirtualEditor``. This module remains as an
import shim so ``from magiceditor.ui.text_editor import TextEditor`` does
not crash. Instantiating ``TextEditor`` is an error.
"""

from __future__ import annotations


class TextEditor:
    """Removed. Use ``VirtualEditor`` (J2.2)."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise RuntimeError("TextEditor was removed; use VirtualEditor")
