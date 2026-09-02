"""Selection-scoped text transforms (case / Base64 / URL) for the Edit menu.

UI-thin: resolves the active selection, delegates the transform to
``core.text_transform`` and writes the result back through the editor.
No selection (or read-only editor) means a no-op — actions are also
disabled in that state by the menu sync.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from magiceditor.core import text_transform as tt

if TYPE_CHECKING:
    from magiceditor.ui.virtual_editor import VirtualEditor

Transform = Callable[[str], str]

CASE_TRANSFORMS: dict[str, Transform] = {
    "upper": tt.to_upper,
    "lower": tt.to_lower,
    "title": tt.to_title_case,
    "sentence": tt.to_sentence_case,
    "invert": tt.invert_case,
}

ENCODE_TRANSFORMS: dict[str, Transform] = {
    "base64_encode": tt.base64_encode,
    "base64_decode": tt.base64_decode,
    "url_encode": tt.url_encode,
    "url_decode": tt.url_decode,
}


def transform_selection(editor: VirtualEditor, transform: Transform) -> bool:
    """Replace the editor selection with ``transform(text)``.

    Returns False (no-op) when there is no selection or the editor is
    read-only. The transform runs before any mutation, so a raising
    transform (e.g. invalid Base64) leaves the document untouched.
    Multi-line selections are supported; the result is inserted at the
    selection start.
    """
    if getattr(editor, "_read_only", False):
        return False
    if not editor.has_selection():
        return False
    text = editor.selected_text()
    if not text:
        return False
    new_text = transform(text)
    editor._delete_selection(emit=False)
    editor._insert_at_cursor(new_text)
    return True
