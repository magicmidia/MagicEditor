"""Basic snippet expansion (Tab trigger)."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Snippet:
    trigger: str
    body: str  # uses $0 for final cursor; $1 placeholders simple
    language: str = "*"  # * = all


_BUILTIN: list[Snippet] = [
    Snippet("fun", "function ${1:name}($2) {\n\t$0\n}\n", "javascript"),
    Snippet("fn", "fn ${1:name}($2) {\n\t$0\n}\n", "rust"),
    Snippet("def", "def ${1:name}($2):\n\t$0\n", "python"),
    Snippet("class", "class ${1:Name}:\n\tdef __init__(self$2):\n\t\t$0\n", "python"),
    Snippet("for", "for ${1:item} in ${2:iterable}:\n\t$0\n", "python"),
    Snippet("if", "if ${1:condition}:\n\t$0\n", "python"),
    Snippet("log", "console.log($1);$0", "javascript"),
    Snippet(
        "html5",
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
        "\t<meta charset=\"UTF-8\">\n\t<title>$1</title>\n"
        "</head>\n<body>\n\t$0\n</body>\n</html>\n",
        "html",
    ),
    Snippet("mdh", "# $1\n\n$0\n", "markdown"),
    Snippet("todo", "# TODO: $0", "*"),
]


def list_snippets(language: str | None = None) -> list[Snippet]:
    lang = (language or "*").lower()
    out: list[Snippet] = []
    for s in _BUILTIN:
        if s.language in ("*", lang):
            out.append(s)
    return out


def expand_snippet(body: str) -> tuple[str, int]:
    """Expand snippet body to plain text and final cursor offset (char).

    Strips ``$0`` / ``${n:...}`` / ``$n`` placeholders simply.
    Returns (text, cursor_index_at_$0_or_end).
    """
    cursor = len(body)
    # Find $0 position first
    m0 = re.search(r"\$0", body)
    if m0:
        cursor = m0.start()

    def repl_named(m: re.Match[str]) -> str:
        return m.group(1)

    text = re.sub(r"\$\{(\d+):([^}]*)\}", repl_named, body)
    text = re.sub(r"\$\d+", "", text)
    # Adjust cursor if we removed content before it
    # Recompute: expand without $0 then find
    without = re.sub(r"\$\{(\d+):([^}]*)\}", repl_named, body)
    m0b = re.search(r"\$0", without)
    if m0b:
        cursor = m0b.start()
        without = without[: m0b.start()] + without[m0b.end() :]
        without = re.sub(r"\$\d+", "", without)
        text = without
    else:
        text = re.sub(r"\$\d+", "", text)
        cursor = len(text)
    return text, max(0, min(cursor, len(text)))


def match_trigger(prefix: str, language: str) -> Snippet | None:
    """Longest trigger match for word prefix."""
    if not prefix:
        return None
    best: Snippet | None = None
    for s in list_snippets(language):
        if (prefix == s.trigger or prefix.endswith(s.trigger)) and (
            best is None or len(s.trigger) > len(best.trigger)
        ):
            best = s
    return best
