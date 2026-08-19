"""CLI entry: ``python -m magiceditor``."""

from __future__ import annotations

import logging
import sys


def main() -> int:
    from magiceditor.services.app_log import setup_logging

    setup_logging()
    try:
        from magiceditor.app import run

        return run(sys.argv)
    except Exception:
        logging.getLogger("magiceditor").exception("Fatal error during startup")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
