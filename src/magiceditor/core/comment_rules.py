"""Language-aware line/block comment markers and toggle transform."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CommentStyle:
    line: str | None = None  # e.g. "//" or "#"
    block_start: str | None = None  # e.g. "/*"
    block_end: str | None = None  # e.g. "*/"


_STYLES: dict[str, CommentStyle] = {
    "python": CommentStyle(line="#"),
    "ruby": CommentStyle(line="#"),
    "shell": CommentStyle(line="#"),
    "bash": CommentStyle(line="#"),
    "powershell": CommentStyle(line="#"),
    "yaml": CommentStyle(line="#"),
    "toml": CommentStyle(line="#"),
    "ini": CommentStyle(line=";"),
    "cfg": CommentStyle(line="#"),
    "sql": CommentStyle(line="--", block_start="/*", block_end="*/"),
    "lua": CommentStyle(line="--", block_start="--[[", block_end="]]"),
    "html": CommentStyle(block_start="<!--", block_end="-->"),
    "xml": CommentStyle(block_start="<!--", block_end="-->"),
    "markdown": CommentStyle(line="<!--", block_start="<!--", block_end="-->"),
    "css": CommentStyle(block_start="/*", block_end="*/"),
    "scss": CommentStyle(line="//", block_start="/*", block_end="*/"),
    "javascript": CommentStyle(line="//", block_start="/*", block_end="*/"),
    "typescript": CommentStyle(line="//", block_start="/*", block_end="*/"),
    "java": CommentStyle(line="//", block_start="/*", block_end="*/"),
    "c": CommentStyle(line="//", block_start="/*", block_end="*/"),
    "cpp": CommentStyle(line="//", block_start="/*", block_end="*/"),
    "csharp": CommentStyle(line="//", block_start="/*", block_end="*/"),
    "go": CommentStyle(line="//", block_start="/*", block_end="*/"),
    "rust": CommentStyle(line="//", block_start="/*", block_end="*/"),
    "php": CommentStyle(line="//", block_start="/*", block_end="*/"),
    "json": CommentStyle(line="//"),
    "plaintext": CommentStyle(line="#"),
}


def comment_style_for(language: str) -> CommentStyle:
    """Return comment style for ``language`` id (case-insensitive)."""
    key = (language or "plaintext").strip().lower()
    if key in _STYLES:
        return _STYLES[key]
    # aliases
    aliases = {
        "js": "javascript",
        "ts": "typescript",
        "py": "python",
        "c++": "cpp",
        "c#": "csharp",
        "cs": "csharp",
        "md": "markdown",
        "txt": "plaintext",
        "text": "plaintext",
        "sh": "shell",
        "ps1": "powershell",
    }
    mapped = aliases.get(key)
    if mapped and mapped in _STYLES:
        return _STYLES[mapped]
    return CommentStyle(line="//")


def _line_is_commented(line: str, marker: str) -> bool:
    stripped = line.lstrip()
    return stripped.startswith(marker)


def toggle_line_comments(lines: list[str], language: str) -> list[str]:
    """Toggle line comments for a contiguous range of lines.

    If every non-blank line is already commented, uncomment; otherwise comment.
    Blank lines are left unchanged.
    """
    style = comment_style_for(language)
    marker = style.line
    if not marker:
        # fall back to block wrap for HTML-like
        if style.block_start and style.block_end and lines:
            joined = "\n".join(lines)
            bs, be = style.block_start, style.block_end
            if joined.strip().startswith(bs) and joined.strip().endswith(be):
                inner = joined.strip()
                inner = inner[len(bs) :]
                if inner.endswith(be):
                    inner = inner[: -len(be)]
                return inner.split("\n") if inner else [""]
            return [f"{bs}{joined}{be}"]
        return list(lines)

    non_blank = [ln for ln in lines if ln.strip()]
    if not non_blank:
        return list(lines)

    all_commented = all(_line_is_commented(ln, marker) for ln in non_blank)
    out: list[str] = []
    for line in lines:
        if not line.strip():
            out.append(line)
            continue
        if all_commented:
            # remove first marker occurrence after indent
            indent_len = len(line) - len(line.lstrip())
            indent = line[:indent_len]
            rest = line[indent_len:]
            if rest.startswith(marker):
                rest = rest[len(marker) :]
                if rest.startswith(" "):
                    rest = rest[1:]
            out.append(indent + rest)
        else:
            indent_len = len(line) - len(line.lstrip())
            indent = line[:indent_len]
            rest = line[indent_len:]
            out.append(f"{indent}{marker} {rest}")
    return out
