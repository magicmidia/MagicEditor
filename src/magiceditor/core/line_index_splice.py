"""Update a line index around a newline edit without copying the suffix.

The index still describes the buffer *before* the edit. The piece table is
already updated. A few bytes around the edit are rescanned, including both
bytes of a CRLF the margin would otherwise split. Every other line only
shifts its offsets, so a newline near the start of a huge line stays cheap
and still matches ``LineIndex.from_bytes``.
"""

from __future__ import annotations

import array

from magiceditor.core.line_index import LineIndex
from magiceditor.core.piece_table import PieceTable


def note_insert(index: LineIndex, table: PieceTable, offset: int, data: bytes) -> None:
    if _insert_is_structural(table, offset, data):
        apply_structural_edit(index, table, offset, 0, data)
    else:
        index.apply_insert_plain(offset, len(data))


def note_delete(index: LineIndex, table: PieceTable, offset: int, deleted: bytes) -> None:
    if _delete_is_structural(table, offset, deleted):
        apply_structural_edit(index, table, offset, len(deleted), b"")
    else:
        index.apply_delete_plain(offset, len(deleted))


def _insert_is_structural(table: PieceTable, offset: int, data: bytes) -> bool:
    if b"\n" in data or b"\r" in data:
        return True
    # A byte between CR and LF splits one CRLF into two breaks.
    if offset <= 0 or offset + len(data) >= len(table):
        return False
    return table.get_text(offset - 1, 1) == b"\r" and table.get_text(offset + len(data), 1) == b"\n"


def _delete_is_structural(table: PieceTable, offset: int, deleted: bytes) -> bool:
    if b"\n" in deleted or b"\r" in deleted:
        return True
    # Deleting the byte between CR and LF merges them into one break.
    if offset <= 0 or offset >= len(table):
        return False
    return table.get_text(offset - 1, 1) == b"\r" and table.get_text(offset, 1) == b"\n"


def apply_structural_edit(
    index: LineIndex,
    table: PieceTable,
    old_offset: int,
    old_deleted: int,
    inserted: bytes,
) -> None:
    old_len = index._length
    delta = len(inserted) - old_deleted
    new_len = old_len + delta
    touch = old_offset - 1 if old_offset > 0 else 0
    # A one-byte margin splits CRLF into a lone CR plus a following LF.
    # Pull the window back over that CR, and forward over a following LF.
    window_start = touch
    if (
        touch > 0
        and table.get_text(touch, 1) == b"\n"
        and table.get_text(touch - 1, 1) == b"\r"
    ):
        window_start = touch - 1
    line0 = index.offset_to_line(window_start)
    old_after = old_offset + old_deleted
    if old_after < old_len:
        surviving = 1
        first_new = old_offset + len(inserted)
        if (
            first_new < new_len
            and table.get_text(first_new, 1) == b"\r"
            and old_after + 1 < old_len
        ):
            surviving = 2
        survivor = old_after + surviving
        if survivor >= old_len:
            window_end = new_len
            survivor = None
        else:
            window_end = old_offset + len(inserted) + surviving
    else:
        window_end = new_len
        survivor = None

    window = table.get_text(window_start, max(0, window_end - window_start))
    sub = LineIndex.from_bytes(window)
    if survivor is None:
        cont_end = new_len
        suffix_from = index.line_count
    else:
        cont_line = index.offset_to_line(survivor)
        cont_end = index._content_ends[cont_line] + delta
        suffix_from = cont_line + 1

    starts = array.array("q", index._starts[:line0])
    ends = array.array("q", index._content_ends[:line0])
    sub_n = sub.line_count
    for k in range(sub_n):
        last = k == sub_n - 1
        if k == 0:
            abs_start = index._starts[line0]
        else:
            abs_start = window_start + sub._starts[k]
        if last:
            abs_end = cont_end
        else:
            abs_end = window_start + sub._content_ends[k]
        starts.append(abs_start)
        ends.append(abs_end)
    for i in range(suffix_from, index.line_count):
        starts.append(index._starts[i] + delta)
        ends.append(index._content_ends[i] + delta)
    index._starts = starts
    index._content_ends = ends
    index._length = new_len
