"""Markdown → HTML for the in-app preview (Qt rich-text subset)."""

from __future__ import annotations

import re

import markdown as md

from magiceditor.preview.sanitize import sanitize_html

_EXTENSIONS = (
    "sane_lists",
    "nl2br",
    "toc",
    "admonition",
    "smarty",
    "tables",
    "fenced_code",
    "footnotes",
    "def_list",
    "attr_list",
)
_FRONTMATTER = re.compile(r"\A---[ \t]*\r?\n.*?\r?\n---[ \t]*\r?\n", re.DOTALL)
_STRIKE = re.compile(r"~~([^~\n]+)~~")
_TASK_LI = re.compile(
    r"(<li>)\[([ xX])\][ \t]+",
    re.IGNORECASE,
)
_BARE_URL = re.compile(
    r'(?<!href=")(?<!">)(?P<url>https?://[^\s<>"\']+)',
)


def strip_frontmatter(source: str) -> str:
    return _FRONTMATTER.sub("", source, count=1)


def _apply_strikethrough(source: str) -> str:
    out: list[str] = []
    in_fence = False
    for line in source.splitlines(keepends=True):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        out.append(_STRIKE.sub(r"<del>\1</del>", line))
    return "".join(out)


def _apply_task_lists(html: str) -> str:
    def repl(match: re.Match[str]) -> str:
        mark = "☑" if match.group(2).lower() == "x" else "☐"
        return f"{match.group(1)}{mark} "

    return _TASK_LI.sub(repl, html)


def _apply_autolink(html: str) -> str:
    return _BARE_URL.sub(r'<a href="\g<url>">\g<url></a>', html)


def _available_extensions() -> list[str]:
    found: list[str] = []
    for name in _EXTENSIONS:
        try:
            md.markdown("x", extensions=[name])
        except Exception:
            continue
        found.append(name)
    return found


_LOADED_EXTS: list[str] | None = None


def loaded_extensions() -> list[str]:
    global _LOADED_EXTS
    if _LOADED_EXTS is None:
        _LOADED_EXTS = _available_extensions()
    return _LOADED_EXTS


def render_markdown(source: str) -> str:
    """Convert Markdown (GFM-ish) to HTML string."""
    text = strip_frontmatter(source or "")
    text = _apply_strikethrough(text)
    html = md.markdown(text, extensions=loaded_extensions())
    html = _apply_task_lists(html)
    return sanitize_html(_apply_autolink(html))
