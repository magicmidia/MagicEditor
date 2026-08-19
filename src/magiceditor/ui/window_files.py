"""File/workspace open policy for MainWindow (J1.2 / L8)."""

from __future__ import annotations

from pathlib import Path


def resolve_open_target(path: str | Path) -> tuple[str, Path]:
    """Return ('workspace', dir) or ('file', file)."""
    target = Path(path)
    if target.is_dir():
        return "workspace", target
    return "file", target


def apply_save_prefs(text: str, *, trim: bool, final_nl: bool) -> str:
    """Apply trim-trailing / final-newline prefs (J1.2 save wiring)."""
    new = text
    if trim:
        ends_nl = text.endswith("\n") or text.endswith("\r\n")
        lines = [ln.rstrip(" \t") for ln in text.splitlines()]
        new = "\n".join(lines)
        if ends_nl:
            new = new + "\n"
    if final_nl and new and not new.endswith(("\n", "\r")):
        new = new + "\n"
    return new


def same_open_path(existing: Path | None, target: Path) -> bool:
    """True when an already-open document is the same filesystem path."""
    if existing is None:
        return False
    try:
        return existing.resolve() == target.resolve()
    except OSError:
        return existing == target


def index_of_open_path(open_paths: list[Path | None], target: Path) -> int | None:
    """Index of ``target`` in the open-tab path list, or None."""
    for i, existing in enumerate(open_paths):
        if same_open_path(existing, target):
            return i
    return None


def apply_save_prefs_to_document(document, *, trim: bool, final_nl: bool) -> bool:
    """Mutate the document buffer when save prefs change the text.

    Returns True if the buffer was rewritten (caller refreshes the viewport).
    Huge files never go through ``document.text()`` (capped at 2 MB).
    """
    if document.huge_mode:
        return _apply_save_prefs_huge(document, trim=trim, final_nl=final_nl)
    from magiceditor.core.piece_table import PieceTable

    text = document.text()
    new = apply_save_prefs(text, trim=trim, final_nl=final_nl)
    if new == text:
        return False
    document.buffer = PieceTable(new)
    document.invalidate_line_index()
    document.mark_modified()
    return True


def _apply_save_prefs_huge(document, *, trim: bool, final_nl: bool) -> bool:
    """Trim / final-newline on the piece table without materializing a str."""
    changed = False
    if trim:
        idx = document.line_index()
        for line in range(idx.line_count - 1, -1, -1):
            start = idx.line_start(line)
            length = idx.line_length(line)
            if length <= 0:
                continue
            raw = document.buffer.get_text(start, length)
            stripped = raw.rstrip(b" \t")
            drop = length - len(stripped)
            if drop:
                document.delete_bytes(start + len(stripped), drop)
                changed = True
                idx = document.line_index()
    if final_nl and len(document.buffer) > 0:
        last = document.buffer.get_text(len(document.buffer) - 1, 1)
        if last not in {b"\n", b"\r"}:
            document.insert_bytes(len(document.buffer), b"\n")
            changed = True
    return changed
