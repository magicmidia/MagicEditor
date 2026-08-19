"""Atomic file writes (temp + replace)."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterable
from pathlib import Path


def write_bytes_atomic(path: Path | str, data: bytes) -> Path:
    """Write ``data`` to ``path`` via a same-directory temp file then replace."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".me-", suffix=".tmp", dir=str(target.parent))
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, target)
    except Exception:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return target


def write_chunks_atomic(path: Path | str, chunks: Iterable[bytes]) -> Path:
    """Write iterable of bytes via temp + replace (K15)."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".me-", suffix=".tmp", dir=str(target.parent))
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            for chunk in chunks:
                if chunk:
                    handle.write(chunk)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, target)
    except Exception:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return target
