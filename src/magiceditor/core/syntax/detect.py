"""Detect language id from file path / name — catalog lives in JSON."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from magiceditor.paths import resource_root


@lru_cache(maxsize=1)
def _catalog() -> tuple[dict[str, str], dict[str, str]]:
    path = resource_root() / "resources" / "syntax" / "extensions.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    exts = {str(k): str(v) for k, v in dict(data.get("extensions") or {}).items()}
    bases = {str(k): str(v) for k, v in dict(data.get("basenames") or {}).items()}
    return exts, bases


def _ext_map() -> dict[str, str]:
    return _catalog()[0]


def _basename_map() -> dict[str, str]:
    return _catalog()[1]


def __getattr__(name: str) -> dict[str, str]:
    if name == "_EXT_MAP":
        return _ext_map()
    if name == "_BASENAME_MAP":
        return _basename_map()
    raise AttributeError(name)


def detect_language(path: str | Path | None, title: str = "") -> str:
    """Return language id from path or title; default ``text``."""
    name = ""
    if path is not None:
        name = Path(path).name
    if not name and title:
        name = title
    if not name:
        return "text"
    base = name.lower()
    bases = _basename_map()
    if base in bases:
        return bases[base]
    exts = _ext_map()
    if base.count(".") >= 2:
        for i in range(base.count(".")):
            part = base.split(".", i + 1)[-1]
            if part in exts:
                return exts[part]
    suffix = Path(name).suffix.lower().lstrip(".")
    if not suffix and "." in name:
        suffix = name.rsplit(".", 1)[-1].lower()
    return exts.get(suffix, "text")


def language_label(lang_id: str) -> str:
    labels = {
        "python": "Python",
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "json": "JSON",
        "markdown": "Markdown",
        "html": "HTML",
        "xml": "XML",
        "css": "CSS",
        "sql": "SQL",
        "c": "C",
        "cpp": "C++",
        "csharp": "C#",
        "java": "Java",
        "go": "Go",
        "rust": "Rust",
        "ruby": "Ruby",
        "php": "PHP",
        "shell": "Shell",
        "powershell": "PowerShell",
        "yaml": "YAML",
        "toml": "TOML",
        "ini": "INI",
        "text": "Plain Text",
        "log": "Log",
        "kotlin": "Kotlin",
        "swift": "Swift",
        "lua": "Lua",
        "r": "R",
        "dart": "Dart",
        "vue": "Vue",
        "svelte": "Svelte",
        "dockerfile": "Dockerfile",
        "makefile": "Makefile",
        "batch": "Batch",
        "graphql": "GraphQL",
        "cmake": "CMake",
        "perl": "Perl",
        "scala": "Scala",
        "haskell": "Haskell",
        "elixir": "Elixir",
        "erlang": "Erlang",
        "clojure": "Clojure",
        "fsharp": "F#",
        "vb": "Visual Basic",
        "objectivec": "Objective-C",
        "julia": "Julia",
        "nim": "Nim",
        "zig": "Zig",
        "solidity": "Solidity",
        "terraform": "Terraform",
        "nginx": "Nginx",
        "apache": "Apache",
        "diff": "Diff",
        "git": "Git",
        "csv": "CSV",
        "tsv": "TSV",
        "properties": "Properties",
        "env": "Env",
        "lock": "Lockfile",
        "image": "Image",
        "font": "Font",
        "binary": "Binary",
        "archive": "Archive",
        "pdf": "PDF",
        "react": "React",
        "angular": "Angular",
        "nodejs": "Node.js",
    }
    return labels.get(lang_id, lang_id.replace("_", " ").title())


def supported_languages() -> list[tuple[str, str]]:
    """Return (id, label) for highlightable / menu languages (not binary assets)."""
    skip = {"image", "font", "binary", "archive", "pdf", "lock"}
    ids = sorted(
        (set(_ext_map().values()) | set(_basename_map().values())) - skip,
        key=language_label,
    )
    if "text" not in ids:
        ids.append("text")
        ids.sort(key=language_label)
    return [(i, language_label(i)) for i in ids]
