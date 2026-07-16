"""Detect language id from file path / name."""

from __future__ import annotations

from pathlib import Path

# extension (lowercase, no dot) -> language id
_EXT_MAP: dict[str, str] = {
    "py": "python",
    "pyw": "python",
    "pyi": "python",
    "js": "javascript",
    "mjs": "javascript",
    "cjs": "javascript",
    "ts": "typescript",
    "tsx": "typescript",
    "jsx": "javascript",
    "json": "json",
    "md": "markdown",
    "markdown": "markdown",
    "html": "html",
    "htm": "html",
    "xml": "xml",
    "svg": "xml",
    "css": "css",
    "scss": "css",
    "sql": "sql",
    "c": "c",
    "h": "c",
    "cpp": "cpp",
    "cc": "cpp",
    "cxx": "cpp",
    "hpp": "cpp",
    "cs": "csharp",
    "java": "java",
    "go": "go",
    "rs": "rust",
    "rb": "ruby",
    "php": "php",
    "sh": "shell",
    "bash": "shell",
    "zsh": "shell",
    "ps1": "powershell",
    "yml": "yaml",
    "yaml": "yaml",
    "toml": "toml",
    "ini": "ini",
    "cfg": "ini",
    "txt": "text",
    "log": "text",
    "csv": "text",
}


def detect_language(path: str | Path | None, title: str = "") -> str:
    """Return language id from path or title; default ``text``."""
    name = ""
    if path is not None:
        name = Path(path).name
    if not name and title:
        name = title
    if not name:
        return "text"
    # multi-dot: take last suffix
    suffix = Path(name).suffix.lower().lstrip(".")
    if not suffix and "." in name:
        suffix = name.rsplit(".", 1)[-1].lower()
    return _EXT_MAP.get(suffix, "text")


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
    }
    return labels.get(lang_id, lang_id.title())


def supported_languages() -> list[tuple[str, str]]:
    """Return (id, label) sorted by label."""
    ids = sorted(set(_EXT_MAP.values()) | {"text"}, key=language_label)
    return [(i, language_label(i)) for i in ids]
