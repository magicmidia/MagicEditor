"""Line moves without materializing the whole document (K14)."""

from __future__ import annotations

from magiceditor.core.document import Document
from magiceditor.core.document_edit import read_lines, replace_line_range


def swap_line_with_neighbor(doc: Document, line: int, *, up: bool) -> int:
    """Swap ``line`` with the neighbor. Returns the new line index."""
    total = doc.line_index().line_count
    if total <= 1:
        return line
    if up:
        if line <= 0:
            return line
        a, b = line - 1, line
        dest = line - 1
    else:
        if line >= total - 1:
            return line
        a, b = line, line + 1
        dest = line + 1
    pair = read_lines(doc, a, b + 1)
    if len(pair) < 2:
        return line
    replace_line_range(doc, a, b + 1, [pair[1], pair[0]])
    return dest
