"""CLI entry: ``python -m magiceditor``."""

from __future__ import annotations

import sys


def main() -> int:
    from magiceditor.app import run

    return run(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
