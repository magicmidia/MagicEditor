"""Theme-bundle JSON I/O (J2.7) — no Qt."""

from __future__ import annotations

import json
from pathlib import Path


def theme_bundle_dict(theme: str, icon_pack: str) -> dict[str, str]:
    return {"theme": theme, "icon_pack": icon_pack}


def parse_theme_bundle(data: dict) -> str | None:
    theme = data.get("theme")
    return str(theme) if theme else None


def write_theme_bundle(path: Path | str, theme: str, icon_pack: str) -> Path:
    target = Path(path)
    payload = theme_bundle_dict(theme, icon_pack)
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return target


def read_theme_bundle(path: Path | str) -> dict:
    raw = Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("theme bundle must be a JSON object")
    return data


def load_imported_theme(path: Path | str) -> str | None:
    return parse_theme_bundle(read_theme_bundle(path))
