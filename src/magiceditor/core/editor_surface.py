"""Common editor surface protocol (tests can implement without Qt)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class EditorSurface(Protocol):
    """Shared operations for the viewport editor (and test doubles)."""

    def goto_line(self, line: int, column: int = 0) -> None: ...

    def has_selection(self) -> bool: ...

    def insert(self, text: str) -> None: ...
