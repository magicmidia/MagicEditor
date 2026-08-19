"""K10: inspect shipped packaging choices (UPX, onedir, lazy datas)."""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def measure_packaging(root: Path | None = None) -> dict[str, bool]:
    """Read spec/scripts and report the cold-start packaging flags."""
    base = root or repo_root()
    onefile = (base / "MagicEditor.spec").read_text(encoding="utf-8")
    onedir = (base / "MagicEditor-onedir.spec").read_text(encoding="utf-8")
    build = (base / "scripts" / "build.ps1").read_text(encoding="utf-8")
    return {
        "onefile_upx_off": "upx=False" in onefile,
        "onedir_upx_off": "upx=False" in onedir,
        "onedir_collect": "COLLECT" in onedir,
        "onefile_lazy_datas": "collect_data_files" not in onefile,
        "onedir_spell_datas": "collect_data_files" in onedir and "spellchecker" in onedir,
        "build_onedir_flag": "[switch]$Onedir" in build,
    }
