"""Spell spans computed off the paint path (K3)."""

from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=4096)
def word_is_correct(word: str, lang: str, fingerprint: int) -> bool:
    """Cache key includes engine fingerprint so dict reloads invalidate."""
    return True


def spans_from_engine(engine, text: str) -> tuple[tuple[int, int], ...]:
    if engine is None or not text:
        return ()
    hits = engine.check_text(text)
    return tuple((int(h.start), int(h.end)) for h in hits)


def refresh_visible_spans(editor) -> None:
    if editor._spell is None:
        editor._spell_spans.clear()
        editor.viewport().update()
        return
    first = int(editor.verticalScrollBar().value())
    visible = max(1, editor.viewport().height() // max(1, editor._line_height)) + 2
    total = editor._line_count()
    last = min(total, first + visible)
    dirty = getattr(editor, "_spell_dirty_line", None)
    full = dirty is None
    keep_lo = max(0, first - 40)
    keep_hi = last + 40
    for key in [k for k in editor._spell_spans if k < keep_lo or k >= keep_hi]:
        del editor._spell_spans[key]
    for line in range(first, last):
        if not full and line in editor._spell_spans and line != dirty:
            continue
        try:
            text = editor._doc.line_text(line)
        except IndexError:
            continue
        if text and len(text) <= 4000:
            editor._spell_spans[line] = spans_from_engine(editor._spell, text)
        elif line in editor._spell_spans:
            del editor._spell_spans[line]
    editor._spell_dirty_line = -1
    editor.viewport().update()
