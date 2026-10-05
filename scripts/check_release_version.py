"""Fail when semver sources or the changelog drift apart.

Checks ``version.VERSION``, ``pyproject.toml`` ``[project].version``,
``packaging/inno/MagicEditor.iss`` ``MyAppVersion``, and a Keep a Changelog
heading ``## [VERSION]`` in ``docs/CHANGELOG.md``.

Optional: ``--tag v0.9.8`` must equal ``v`` + VERSION.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from magiceditor.version import VERSION, changelog_contains, parse_semver, release_tag  # noqa: E402


def project_version(text: str) -> str:
    """``[project].version`` from a pyproject.toml body."""
    in_project = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "[project]":
            in_project = True
            continue
        if in_project and stripped.startswith("["):
            break
        if in_project:
            match = re.match(r'version\s*=\s*"([^"]+)"', stripped)
            if match:
                return match.group(1)
    raise ValueError("pyproject.toml has no [project].version")


def inno_version(text: str) -> str:
    """``#define MyAppVersion`` from an Inno Setup script."""
    match = re.search(r'(?m)^[ \t]*#define MyAppVersion "([^"]+)"', text)
    if match is None:
        raise ValueError("Inno script has no MyAppVersion")
    return match.group(1)


def problems(root: Path, tag: str | None = None) -> list[str]:
    """Human-readable mismatches. Empty means the tree is consistent."""
    found: list[str] = []
    try:
        parse_semver(VERSION)
    except ValueError as exc:
        found.append(str(exc))
    pyproject = project_version((root / "pyproject.toml").read_text(encoding="utf-8"))
    installer = inno_version(
        (root / "packaging" / "inno" / "MagicEditor.iss").read_text(encoding="utf-8")
    )
    changelog = (root / "docs" / "CHANGELOG.md").read_text(encoding="utf-8")
    if pyproject != VERSION:
        found.append(f"pyproject.toml version {pyproject!r} != VERSION {VERSION!r}")
    if installer != VERSION:
        found.append(f"Inno MyAppVersion {installer!r} != VERSION {VERSION!r}")
    if not changelog_contains(changelog, VERSION):
        found.append(f"docs/CHANGELOG.md has no heading ## [{VERSION}]")
    if tag is not None and tag != release_tag():
        found.append(f"git tag {tag!r} != {release_tag()!r}")
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check MagicEditor semver lockstep")
    parser.add_argument("--tag", default=None, help="Git tag that must match vVERSION")
    args = parser.parse_args(argv)
    found = problems(ROOT, tag=args.tag)
    if found:
        for item in found:
            print(item, file=sys.stderr)
        return 1
    print(f"semver OK: {VERSION} ({release_tag()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
