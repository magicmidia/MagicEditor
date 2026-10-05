"""Streaming checksums for files and in-memory buffers.

Reads files in binary chunks so arbitrarily large files can be hashed
without loading them fully into memory (mmap/huge-file friendly).
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

DEFAULT_ALGORITHMS: tuple[str, ...] = (
    "md5",
    "sha1",
    "sha256",
    "sha384",
    "sha512",
    "blake2b",
)
DEFAULT_CHUNK_SIZE = 1024 * 1024  # 1 MiB


def _build_hashers(algorithms: Iterable[str]) -> dict[str, hashlib._Hash]:
    """Create one hasher per requested algorithm, validating the names."""
    hashers: dict[str, hashlib._Hash] = {}
    for name in algorithms:
        if name not in hashlib.algorithms_available:
            msg = (
                f"Unsupported hash algorithm: {name!r}. "
                f"See hashlib.algorithms_available for valid names."
            )
            raise ValueError(msg)
        hashers[name] = hashlib.new(name)
    return hashers


def file_hashes(
    path: str | Path,
    algorithms: Iterable[str] = DEFAULT_ALGORITHMS,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> dict[str, str]:
    """Return ``{algorithm: hexdigest}`` for the file at ``path``.

    The file is read in binary chunks of ``chunk_size`` bytes; the whole
    file is never materialized in memory. Raises ``OSError`` (e.g.
    ``FileNotFoundError``) if the file cannot be opened, and ``ValueError``
    for unknown algorithm names or a non-positive ``chunk_size``.
    """
    if chunk_size <= 0:
        msg = f"chunk_size must be positive, got {chunk_size}"
        raise ValueError(msg)
    hashers = _build_hashers(algorithms)
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            for h in hashers.values():
                h.update(chunk)
    return {name: h.hexdigest() for name, h in hashers.items()}


def bytes_hashes(
    data: bytes,
    algorithms: Iterable[str] = DEFAULT_ALGORITHMS,
) -> dict[str, str]:
    """Return ``{algorithm: hexdigest}`` for an in-memory buffer.

    Convenience for small buffers already in memory (e.g. a document
    snapshot or a selection); use :func:`file_hashes` for files on disk.
    Raises ``ValueError`` for unknown algorithm names.
    """
    hashers = _build_hashers(algorithms)
    for h in hashers.values():
        h.update(data)
    return {name: h.hexdigest() for name, h in hashers.items()}
