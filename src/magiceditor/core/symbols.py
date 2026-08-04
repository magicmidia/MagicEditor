"""Lightweight symbol extraction (regex, no full AST)."""

from __future__ import annotations

import re
from dataclasses import dataclass

_PATTERNS: dict[str, list[tuple[str, re.Pattern[str]]]] = {
    "python": [
        ("class", re.compile(r"^\s*class\s+(\w+)", re.M)),
        ("def", re.compile(r"^\s*def\s+(\w+)", re.M)),
        ("async def", re.compile(r"^\s*async\s+def\s+(\w+)", re.M)),
    ],
    "javascript": [
        ("function", re.compile(r"^\s*function\s+(\w+)", re.M)),
        ("class", re.compile(r"^\s*class\s+(\w+)", re.M)),
        ("const", re.compile(r"^\s*(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s*)?\(", re.M)),
    ],
    "typescript": [
        ("function", re.compile(r"^\s*function\s+(\w+)", re.M)),
        ("class", re.compile(r"^\s*class\s+(\w+)", re.M)),
        ("interface", re.compile(r"^\s*interface\s+(\w+)", re.M)),
    ],
    "java": [
        (
            "class",
            re.compile(
                r"^\s*(?:public\s+|private\s+|protected\s+)?class\s+(\w+)", re.M
            ),
        ),
        (
            "method",
            re.compile(
                r"^\s*(?:public|private|protected).+\s+(\w+)\s*\([^;]*\)\s*\{",
                re.M,
            ),
        ),
    ],
    "go": [
        ("func", re.compile(r"^\s*func\s+(?:\([^)]+\)\s+)?(\w+)", re.M)),
        ("type", re.compile(r"^\s*type\s+(\w+)", re.M)),
    ],
    "rust": [
        ("fn", re.compile(r"^\s*(?:pub\s+)?fn\s+(\w+)", re.M)),
        ("struct", re.compile(r"^\s*(?:pub\s+)?struct\s+(\w+)", re.M)),
    ],
    "c": [
        ("func", re.compile(r"^\s*\w[\w\s\*]+?\s+(\w+)\s*\([^;]*\)\s*\{", re.M)),
    ],
    "cpp": [
        ("func", re.compile(r"^\s*\w[\w\s:\*&<>]+?\s+(\w+)\s*\([^;]*\)\s*\{", re.M)),
        ("class", re.compile(r"^\s*class\s+(\w+)", re.M)),
    ],
    "markdown": [
        ("heading", re.compile(r"^(#{1,6})\s+(.+)$", re.M)),
    ],
    "sql": [
        (
            "create",
            re.compile(
                r"^\s*create\s+(?:or\s+replace\s+)?"
                r"(?:table|view|function|procedure)\s+(\w+)",
                re.I | re.M,
            ),
        ),
    ],
}


@dataclass(frozen=True, slots=True)
class Symbol:
    name: str
    kind: str
    line: int  # 1-based


def extract_symbols(text: str, language: str, *, max_symbols: int = 500) -> list[Symbol]:
    """Extract symbols from text; stops after ``max_symbols`` (huge-file guard)."""
    key = (language or "plaintext").strip().lower()
    aliases = {
        "js": "javascript",
        "ts": "typescript",
        "py": "python",
        "md": "markdown",
        "c++": "cpp",
    }
    key = aliases.get(key, key)
    patterns = _PATTERNS.get(key)
    if not patterns:
        return []

    # Limit scan size for huge content
    sample = text if len(text) <= 2_000_000 else text[:2_000_000]
    found: list[Symbol] = []

    if key == "markdown":
        for m in patterns[0][1].finditer(sample):
            level = len(m.group(1))
            name = m.group(2).strip()
            line = sample.count("\n", 0, m.start()) + 1
            found.append(Symbol(name=name, kind=f"h{level}", line=line))
            if len(found) >= max_symbols:
                break
        return found

    for kind, pat in patterns:
        for m in pat.finditer(sample):
            name = m.group(1)
            line = sample.count("\n", 0, m.start()) + 1
            found.append(Symbol(name=name, kind=kind, line=line))
            if len(found) >= max_symbols:
                return sorted(found, key=lambda s: s.line)
    return sorted(found, key=lambda s: s.line)
