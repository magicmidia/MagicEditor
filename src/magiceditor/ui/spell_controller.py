"""Spell context helpers extracted from the power-features mixin (J1.3)."""

from __future__ import annotations

from magiceditor.core.multi_cursor import word_at
from magiceditor.services.session_state import SessionState


def word_on_line(line_text: str, col: int) -> tuple[str, int, int] | None:
    hit = word_at([line_text], 0, col)
    if hit is None:
        return None
    word, start, end = hit
    return word, start, end


def spell_word_at_caret(editor) -> tuple[str, int, int, int] | None:
    """Viewport-safe: only the caret line (not the whole file)."""
    line = editor._cursor_line
    text = editor._doc.line_text(line)
    hit = word_on_line(text, editor._cursor_col)
    if hit is None:
        return None
    word, start, end = hit
    return word, line, start, end


def ignore_word_at_caret(engine, editor) -> str | None:
    """K14: ignore the caret word without reading the whole document."""
    hit = spell_word_at_caret(editor)
    if hit is None:
        return None
    engine.ignore_word(hit[0])
    return hit[0]


def add_word_at_caret(engine, editor) -> str | None:
    """K14: add the caret word to the user dict without reading the whole document."""
    hit = spell_word_at_caret(editor)
    if hit is None:
        return None
    engine.add_to_user_dict(hit[0])
    return hit[0]


def toggle_session_spell(session: SessionState) -> None:
    """Flip spell_check without forcing spell on code files (K3)."""
    session.spell_check = not bool(session.spell_check)
