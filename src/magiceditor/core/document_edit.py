"""Apply pure transforms to a Document without materializing external huge sources.

For huge_mode documents, prefer operating on a line range only.
"""

from __future__ import annotations

from collections.abc import Callable

from magiceditor.core.document import Document
from magiceditor.core.line_ops import lines_to_text, text_to_lines

LineTransform = Callable[[list[str]], list[str]]


def _eol_str(doc: Document) -> str:
    if doc.eol == "CRLF":
        return "\r\n"
    if doc.eol == "CR":
        return "\r"
    return "\n"


def _enc(doc: Document) -> str:
    return doc.encoding if doc.encoding != "utf-8-sig" else "utf-8"


def _ends_with_newline(doc: Document) -> bool:
    n = len(doc.buffer)
    if n <= 0:
        return False
    last = doc.buffer.get_text(n - 1, 1)
    return last in {b"\n", b"\r"}


def read_lines(doc: Document, start: int = 0, end: int | None = None) -> list[str]:
    """Read lines [start, end) as content without trailing newlines."""
    idx = doc.line_index()
    total = idx.line_count
    if end is None:
        end = total
    start = max(0, min(start, total))
    end = max(start, min(end, total))
    return [doc.line_text(i).rstrip("\r\n") for i in range(start, end)]


def replace_line_range(doc: Document, start: int, end: int, new_lines: list[str]) -> None:
    """Replace lines [start, end) with ``new_lines`` (content only)."""
    idx = doc.line_index()
    total = idx.line_count
    start = max(0, min(start, total))
    end = max(start, min(end, total))
    if start >= total and not new_lines:
        return

    if start < total:
        byte_start = idx.line_start(start)
    else:
        byte_start = len(doc.buffer)

    if end < total:
        byte_end = idx.line_start(end)
    else:
        byte_end = len(doc.buffer)

    restore_nl = end >= total and _ends_with_newline(doc)
    eol = _eol_str(doc)
    if new_lines:
        body = lines_to_text(new_lines, eol)
        if (end < total or restore_nl) and not body.endswith(("\n", "\r")):
            body = body + eol
    else:
        body = eol if restore_nl else ""

    enc = _enc(doc)
    data = body.encode(enc, errors="replace")
    length = byte_end - byte_start
    if length > 0:
        doc.delete_bytes(byte_start, length)
    if data:
        doc.insert_bytes(byte_start, data)
    doc.invalidate_line_index()


def transform_line_range(
    doc: Document,
    start: int,
    end: int,
    transform: LineTransform,
) -> None:
    idx = doc.line_index()
    total = idx.line_count
    adj_end = end
    # Trailing empty line from a final newline is not content — don't sort it first.
    if (
        start == 0
        and end >= total
        and total > 0
        and _ends_with_newline(doc)
        and not doc.line_text(total - 1).rstrip("\r\n")
    ):
        adj_end = total - 1
    lines = read_lines(doc, start, adj_end)
    new_lines = transform(lines)
    replace_line_range(doc, start, end, new_lines)


def transform_all_lines(
    doc: Document, transform: LineTransform, *, max_lines: int = 500_000
) -> bool:
    """Transform entire document. Returns False if too large (caller should scope)."""
    total = doc.line_index().line_count
    if total > max_lines:
        return False
    transform_line_range(doc, 0, total, transform)
    return True


def selection_or_all(
    doc: Document,
    *,
    sel_start_line: int | None,
    sel_end_line: int | None,
    transform: LineTransform,
) -> None:
    """Apply transform to selection lines or whole document."""
    total = doc.line_index().line_count
    if sel_start_line is not None and sel_end_line is not None:
        a, b = sorted((sel_start_line, sel_end_line))
        # inclusive end line for editor selection
        transform_line_range(doc, a, min(total, b + 1), transform)
    else:
        transform_line_range(doc, 0, total, transform)


def document_as_lines(doc: Document, *, max_bytes: int = 20_000_000) -> list[str] | None:
    """Materialize lines only if buffer small enough."""
    if len(doc.buffer) > max_bytes:
        return None
    text = doc.text()
    return text_to_lines(text)
