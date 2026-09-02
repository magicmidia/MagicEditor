"""Pure line-oriented transforms (piece-table-safe when applied via Document APIs).

Operates on lists of line *content* strings without trailing newlines.
Never requires loading a multi-GB file as one str when callers feed a line range.
"""

from __future__ import annotations


def move_line_up(lines: list[str], index: int) -> tuple[list[str], int]:
    """Swap line ``index`` with the previous line. Returns (new_lines, new_index)."""
    if index <= 0 or index >= len(lines):
        return list(lines), index
    out = list(lines)
    out[index - 1], out[index] = out[index], out[index - 1]
    return out, index - 1


def move_line_down(lines: list[str], index: int) -> tuple[list[str], int]:
    """Swap line ``index`` with the next line."""
    if index < 0 or index >= len(lines) - 1:
        return list(lines), index
    out = list(lines)
    out[index], out[index + 1] = out[index + 1], out[index]
    return out, index + 1


def sort_lines(lines: list[str], *, reverse: bool = False, ignore_case: bool = False) -> list[str]:
    """Return sorted copy of lines."""
    key = (lambda s: s.casefold()) if ignore_case else None
    return sorted(lines, key=key, reverse=reverse)


def sort_lines_by_length(lines: list[str], *, reverse: bool = False) -> list[str]:
    """Return lines sorted by length (stable: ties keep original order)."""
    return sorted(lines, key=len, reverse=reverse)


def remove_duplicate_lines(lines: list[str]) -> list[str]:
    """Remove duplicate lines, keeping the first occurrence (stable).

    Blank lines are treated as normal lines: removed only when duplicated.
    """
    seen: set[str] = set()
    out: list[str] = []
    for line in lines:
        if line not in seen:
            seen.add(line)
            out.append(line)
    return out


def remove_consecutive_duplicates(lines: list[str]) -> list[str]:
    """Remove only consecutive duplicate lines."""
    out: list[str] = []
    for line in lines:
        if not out or out[-1] != line:
            out.append(line)
    return out


def reverse_lines(lines: list[str]) -> list[str]:
    """Return lines in reverse order."""
    return list(reversed(lines))


def join_lines(lines: list[str], separator: str = " ") -> list[str]:
    """Join all lines into a single line."""
    if not lines:
        return []
    return [separator.join(lines)]


def delete_blank_lines(lines: list[str], *, keep_one: bool = False) -> list[str]:
    """Remove empty / whitespace-only lines.

    If ``keep_one``, collapse consecutive blanks to a single blank line.
    """
    out: list[str] = []
    prev_blank = False
    for line in lines:
        blank = not line.strip()
        if blank:
            if keep_one and not prev_blank:
                out.append("")
            prev_blank = True
            continue
        out.append(line)
        prev_blank = False
    return out


def trim_trailing_whitespace(lines: list[str]) -> list[str]:
    """Strip trailing spaces/tabs on each line (preserve content otherwise)."""
    return [line.rstrip(" \t") for line in lines]


def tabs_to_spaces(lines: list[str], tab_width: int = 4) -> list[str]:
    """Expand tabs to spaces using ``tab_width`` (column-aware per line)."""
    width = max(1, tab_width)
    result: list[str] = []
    for line in lines:
        out: list[str] = []
        col = 0
        for ch in line:
            if ch == "\t":
                spaces = width - (col % width)
                out.append(" " * spaces)
                col += spaces
            else:
                out.append(ch)
                col += 1
        result.append("".join(out))
    return result


def spaces_to_tabs(lines: list[str], tab_width: int = 4) -> list[str]:
    """Convert leading indent spaces to tabs; body spaces left as-is."""
    width = max(1, tab_width)
    result: list[str] = []
    for line in lines:
        i = 0
        while i < len(line) and line[i] == " ":
            i += 1
        leading = line[:i]
        rest = line[i:]
        tabs = len(leading) // width
        rem = len(leading) % width
        result.append(("\t" * tabs) + (" " * rem) + rest)
    return result


def lines_to_text(lines: list[str], eol: str = "\n") -> str:
    """Join lines with ``eol``. No trailing eol unless last line was empty and multi."""
    if not lines:
        return ""
    return eol.join(lines)


def text_to_lines(text: str) -> list[str]:
    """Split text into lines, preserving empty trailing line semantics of splitlines."""
    if not text:
        return [""]
    # splitlines drops final empty if text ends with newline — restore editor semantics
    ends_with_nl = text.endswith("\n") or text.endswith("\r")
    parts = text.splitlines()
    if ends_with_nl:
        parts.append("")
    return parts if parts else [""]
