"""Set the semver in version.py, pyproject.toml, and the Inno script.

Does not commit, tag, or rewrite existing changelog bullets.

Usage:
  uv run python scripts/bump_version.py 0.9.9
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

from magiceditor.version import changelog_contains, parse_semver  # noqa: E402


def _replace_line(path: Path, pattern: str, replacement: str) -> None:
    text = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.M)
    if count != 1:
        raise SystemExit(f"pattern did not match once in {path}")
    path.write_text(updated, encoding="utf-8")


def _ensure_changelog_heading(version: str) -> None:
    path = ROOT / "docs" / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    if changelog_contains(text, version):
        return
    heading = f"## [{version}] — \n\n- \n\n"
    marker = "## [Unreleased]"
    if marker in text:
        text = text.replace(marker, marker + "\n\n" + heading, 1)
    else:
        text = heading + text
    path.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bump MagicEditor semver")
    parser.add_argument("version", help="New semver, e.g. 0.9.9 or 1.0.0-beta.1")
    args = parser.parse_args(argv)
    version = str(parse_semver(args.version))
    _replace_line(
        ROOT / "src" / "magiceditor" / "version.py",
        r'^VERSION: str = "[^"]+"',
        f'VERSION: str = "{version}"',
    )
    _replace_line(
        ROOT / "pyproject.toml",
        r'^version = "[^"]+"',
        f'version = "{version}"',
    )
    _replace_line(
        ROOT / "packaging" / "inno" / "MagicEditor.iss",
        r'^([ \t]*#define MyAppVersion ")[^"]+(")',
        rf'\g<1>{version}\g<2>',
    )
    _ensure_changelog_heading(version)
    print(f"version set to {version}")
    print("Fill docs/CHANGELOG.md, then run scripts/check_release_version.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
