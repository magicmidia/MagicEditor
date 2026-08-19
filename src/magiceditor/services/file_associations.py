"""Windows file association extension list (installer / ProgID source of truth)."""

from __future__ import annotations

import json
from pathlib import Path

# Roadmap I4 text-oriented extensions
DEFAULT_EXTENSIONS: tuple[str, ...] = (
    ".txt",
    ".md",
    ".markdown",
    ".log",
    ".ini",
    ".cfg",
    ".conf",
    ".json",
    ".xml",
    ".yml",
    ".yaml",
    ".csv",
    ".sql",
    ".py",
    ".js",
    ".ts",
    ".html",
    ".css",
    ".cs",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".sh",
    ".ps1",
    ".toml",
    ".env",
    ".gitignore",
    ".editorconfig",
)

PROGID = "MagicEditor.Document"
APP_DESCRIPTION = "MagicEditor Document"

# Windows executable scripts — never steal the default open verb.
NATIVE_SCRIPT_PROGIDS: dict[str, str] = {
    ".bat": "batfile",
    ".cmd": "cmdfile",
}


def association_extensions() -> list[str]:
    return list(DEFAULT_EXTENSIONS)


def association_manifest() -> dict[str, object]:
    return {
        "progid": PROGID,
        "description": APP_DESCRIPTION,
        "extensions": association_extensions(),
        "open_verb": '"%1"',  # placeholder; installer wraps with exe path
    }


def write_manifest(path: Path) -> Path:
    """Write JSON manifest for packaging tools."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(association_manifest(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path
