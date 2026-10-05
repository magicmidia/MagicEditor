"""Allowlist sanitizer for Markdown/HTML preview (no script/iframe/on*)."""

from __future__ import annotations

import re

_ALLOWED = frozenset(
    {
        "a",
        "abbr",
        "b",
        "blockquote",
        "br",
        "code",
        "del",
        "div",
        "em",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "hr",
        "i",
        "img",
        "li",
        "ol",
        "p",
        "pre",
        "span",
        "strong",
        "sub",
        "sup",
        "table",
        "tbody",
        "td",
        "th",
        "thead",
        "tr",
        "ul",
    }
)
_ALLOWED_ATTR = {
    "a": frozenset({"href", "title"}),
    "img": frozenset({"alt", "title", "width", "height"}),
    "td": frozenset({"colspan", "rowspan"}),
    "th": frozenset({"colspan", "rowspan"}),
    "code": frozenset({"class"}),
    "pre": frozenset({"class"}),
    "span": frozenset({"class"}),
    "div": frozenset({"class", "id"}),
    "h1": frozenset({"id"}),
    "h2": frozenset({"id"}),
    "h3": frozenset({"id"}),
    "h4": frozenset({"id"}),
    "h5": frozenset({"id"}),
    "h6": frozenset({"id"}),
}
_BLOCKED_SCHEMES = ("javascript:", "vbscript:", "file:", "ms-msdt:", "data:")
_TAG = re.compile(r"(?s)<(/)?([a-zA-Z][a-zA-Z0-9]*)\b([^>]*)>")
_ATTR = re.compile(r"""([^\s=]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?""")
_REMOTE = re.compile(r"(?i)^(https?:|//)")
# QTextBrowser paints the inside of a removed <style>/<script> as visible text.
_STRIP_CLOSED = re.compile(
    r"(?is)<(script|style|iframe|object|embed|form|noscript)\b[^>]*>.*?</\1\s*>"
)
_STRIP_OPEN = re.compile(r"(?is)<(script|style|iframe|object|embed|form|noscript)\b[^>]*>.*")


def is_safe_href(value: str) -> bool:
    v = (value or "").strip()
    low = v.lower()
    if any(low.startswith(s) for s in _BLOCKED_SCHEMES):
        return False
    if low.startswith("http:") or low.startswith("https:"):
        return True
    if low.startswith("#") or low.startswith("mailto:"):
        return True
    return ":" not in v.split("/", 1)[0]


def sanitize_html(html: str) -> str:
    """Drop script/iframe/on* and remote images; keep a markdown-safe subset."""
    html = _STRIP_CLOSED.sub("", html)
    html = _STRIP_OPEN.sub("", html)

    def repl(match: re.Match[str]) -> str:
        closing, name, attrs = match.group(1), match.group(2).lower(), match.group(3) or ""
        if name in {
            "script",
            "iframe",
            "object",
            "embed",
            "link",
            "meta",
            "style",
            "form",
            "noscript",
        }:
            return ""
        if name not in _ALLOWED:
            return ""
        if closing:
            return f"</{name}>"
        allowed = _ALLOWED_ATTR.get(name, frozenset())
        kept: list[str] = []
        for am in _ATTR.finditer(attrs):
            key = am.group(1).lower()
            if key.startswith("on"):
                continue
            val = am.group(2) or am.group(3) or am.group(4) or ""
            if key not in allowed:
                continue
            if key == "href" and not is_safe_href(val):
                continue
            if name == "img" and key == "src":
                continue
            if _REMOTE.match(val):
                if name == "img":
                    continue
                if key != "href":
                    continue
            kept.append(f'{key}="{val}"')
        extra = (" " + " ".join(kept)) if kept else ""
        return f"<{name}{extra}>"

    return _TAG.sub(repl, html)
