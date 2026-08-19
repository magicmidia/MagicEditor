"""Central product version — single source of truth for UI, packaging, and metadata.

Update VERSION / STAGE here; keep ``pyproject.toml`` ``[project].version`` in sync
with VERSION (PEP 440). Display strings always come from this module.
"""

from __future__ import annotations

# --- Canonical product identity -----------------------------------------
APP_NAME: str = "MagicEditor"
APP_ORG: str = "MagicEditor"

# Semver core (keep aligned with pyproject.toml [project].version)
VERSION: str = "0.9.2"

# Marketing / channel label (empty string for stable releases)
STAGE: str = "BETA"  # e.g. "BETA", "RC1", "" for stable

# Minimum splash visibility (seconds) when splash is enabled
SPLASH_MIN_SECONDS: float = 1.5


def version_core() -> str:
    """Numeric version only, e.g. ``0.9.2``."""
    return VERSION


def version_display() -> str:
    """User-facing string, e.g. ``0.9.2 BETA`` or ``0.9.2``."""
    stage = (STAGE or "").strip()
    if stage:
        return f"{VERSION} {stage}"
    return VERSION


def version_label() -> str:
    """Short status-bar form, e.g. ``v0.9.2 BETA``."""
    return f"v{version_display()}"


def about_version_text(*, prefix: str = "Versão") -> str:
    """About dialog line: ``Versão 0.9.2 BETA``."""
    return f"{prefix} {version_display()}"


def pep440() -> str:
    """Best-effort PEP 440 string for packaging tools.

    BETA → ``0.9.2b0``; empty stage → ``0.9.2``.
    """
    stage = (STAGE or "").strip().upper()
    if not stage:
        return VERSION
    if stage.startswith("BETA") or stage == "B":
        return f"{VERSION}b0"
    if stage.startswith("RC"):
        n = "".join(ch for ch in stage if ch.isdigit()) or "1"
        return f"{VERSION}rc{n}"
    if stage.startswith("ALPHA") or stage == "A":
        return f"{VERSION}a0"
    return VERSION


# Back-compat aliases
__version__ = VERSION
__version_display__ = version_display()
