"""Central product version — single source of truth for UI, packaging, and metadata.

``VERSION`` is a Semantic Version (``MAJOR.MINOR.PATCH``, optional pre-release).
Keep it identical in ``pyproject.toml`` and the Inno ``MyAppVersion`` define.
``STAGE`` is a display channel only (BETA, RC1, or empty) and is not part of
the semver string. Display strings always come from this module.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# --- Canonical product identity -----------------------------------------
APP_NAME: str = "MagicEditor"
APP_ORG: str = "MagicEditor"

# Semver core (keep aligned with pyproject.toml [project].version)
VERSION: str = "0.9.8"

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


# SemVer 2.0.0 (https://semver.org/spec/v2.0.0.html)
_SEMVER_RE = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?P<build>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)
_CHANGELOG_HEADING = re.compile(r"(?m)^## \[([^\]]+)\]")


@dataclass(frozen=True)
class SemVer:
    """Parsed Semantic Version."""

    major: int
    minor: int
    patch: int
    prerelease: str = ""
    build: str = ""

    def __str__(self) -> str:
        text = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            text = f"{text}-{self.prerelease}"
        if self.build:
            text = f"{text}+{self.build}"
        return text


def parse_semver(value: str) -> SemVer:
    """Parse a SemVer 2.0.0 string. Raises ``ValueError`` when it is not one."""
    match = _SEMVER_RE.match(value.strip())
    if match is None:
        raise ValueError(f"not a semantic version: {value!r}")
    return SemVer(
        major=int(match.group("major")),
        minor=int(match.group("minor")),
        patch=int(match.group("patch")),
        prerelease=match.group("prerelease") or "",
        build=match.group("build") or "",
    )


def semver() -> SemVer:
    """Parsed product version. Fails fast if ``VERSION`` drifts off semver."""
    return parse_semver(VERSION)


def release_tag(version: str | None = None) -> str:
    """Git tag for a release, e.g. ``v0.9.8``."""
    text = VERSION if version is None else version.strip()
    parse_semver(text)
    return f"v{text}"


def changelog_contains(text: str, version: str | None = None) -> bool:
    """True when a Keep a Changelog heading matches the version exactly."""
    wanted = (VERSION if version is None else version).strip()
    return any(match.group(1).strip() == wanted for match in _CHANGELOG_HEADING.finditer(text))


def changelog_section(text: str, version: str | None = None) -> str:
    """Body of the Keep a Changelog section for ``version``, including the heading."""
    wanted = (VERSION if version is None else version).strip()
    lines = text.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if line.startswith(f"## [{wanted}]"):
            start = index
            break
    if start is None:
        return ""
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return "\n".join(lines[start:end]).strip() + "\n"


# Back-compat aliases
__version__ = VERSION
__version_display__ = version_display()
