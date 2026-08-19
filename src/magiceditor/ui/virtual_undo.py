"""Undo/redo stack for the virtual editor (no Qt)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

MAX_UNDO = 500

Kind = Literal["insert", "delete"]


@dataclass(slots=True)
class EditOp:
    kind: Kind
    offset: int
    data: bytes


class UndoHistory:
    """Bounded insert/delete history. ``applying`` skips new records."""

    def __init__(self, max_ops: int = MAX_UNDO) -> None:
        self._max = max(1, int(max_ops))
        self._undo: list[EditOp] = []
        self._redo: list[EditOp] = []
        self.applying = False

    def __len__(self) -> int:
        return len(self._undo)

    def can_undo(self) -> bool:
        return bool(self._undo)

    def can_redo(self) -> bool:
        return bool(self._redo)

    def push(self, op: EditOp) -> None:
        if self.applying:
            return
        self._undo.append(op)
        if len(self._undo) > self._max:
            self._undo = self._undo[-self._max :]
        self._redo.clear()

    def record_insert(self, offset: int, data: bytes) -> None:
        if data:
            self.push(EditOp("insert", offset, data))

    def record_delete(self, offset: int, data: bytes) -> None:
        if data:
            self.push(EditOp("delete", offset, data))

    def pop_undo(self) -> EditOp | None:
        return self._undo.pop() if self._undo else None

    def pop_redo(self) -> EditOp | None:
        return self._redo.pop() if self._redo else None

    def remember_undone(self, op: EditOp) -> None:
        self._redo.append(op)

    def remember_redone(self, op: EditOp) -> None:
        self._undo.append(op)


def apply_undo_op(
    op: EditOp,
    *,
    insert_bytes,
    delete_bytes,
) -> int:
    """Invert ``op`` on a buffer. Returns caret byte offset."""
    if op.kind == "insert":
        delete_bytes(op.offset, len(op.data))
        return op.offset
    insert_bytes(op.offset, op.data)
    return op.offset


def apply_redo_op(
    op: EditOp,
    *,
    insert_bytes,
    delete_bytes,
) -> int:
    """Replay ``op``. Returns caret byte offset."""
    if op.kind == "insert":
        insert_bytes(op.offset, op.data)
        return op.offset + len(op.data)
    delete_bytes(op.offset, len(op.data))
    return op.offset


def undo_editor(editor) -> bool:
    """Apply one undo on a virtual-editor duck. Returns False if empty."""
    history: UndoHistory = editor._history
    op = history.pop_undo()
    if op is None:
        return False
    history.applying = True
    try:
        caret = apply_undo_op(
            op,
            insert_bytes=editor._doc.insert_bytes,
            delete_bytes=editor._doc.delete_bytes,
        )
        history.remember_undone(op)
        editor._place_cursor_at(caret)
        editor._emit_edit(clear_redo=False)
    finally:
        history.applying = False
    return True


def redo_editor(editor) -> bool:
    history: UndoHistory = editor._history
    op = history.pop_redo()
    if op is None:
        return False
    history.applying = True
    try:
        caret = apply_redo_op(
            op,
            insert_bytes=editor._doc.insert_bytes,
            delete_bytes=editor._doc.delete_bytes,
        )
        history.remember_redone(op)
        editor._place_cursor_at(caret)
        editor._emit_edit(clear_redo=False)
    finally:
        history.applying = False
    return True


def track_insert(editor, offset: int, data: bytes) -> None:
    if not data:
        return
    editor._doc.insert_bytes(offset, data)
    editor._history.record_insert(offset, data)


def track_delete(editor, offset: int, length: int) -> None:
    if length <= 0:
        return
    deleted = editor._doc.buffer.get_text(offset, length)
    editor._doc.delete_bytes(offset, length)
    editor._history.record_delete(offset, deleted)
