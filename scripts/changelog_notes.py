"""Print the Keep a Changelog section for the current semver.

Usage:
  uv run python scripts/changelog_notes.py
  uv run python scripts/changelog_notes.py --out release-notes.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from magiceditor.version import VERSION, changelog_section  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract changelog notes for VERSION")
    parser.add_argument("--out", type=Path, default=None, help="Write notes to this file")
    args = parser.parse_args(argv)
    text = (ROOT / "docs" / "CHANGELOG.md").read_text(encoding="utf-8")
    notes = changelog_section(text, VERSION)
    if not notes.strip():
        print(f"no changelog section for {VERSION}", file=sys.stderr)
        return 1
    if args.out is None:
        sys.stdout.write(notes)
    else:
        args.out.write_text(notes, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
