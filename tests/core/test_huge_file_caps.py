"""N3: huge-file paths stay fail-closed (no full str of >50MB)."""

from pathlib import Path

import pytest

from magiceditor.core.document import Document
from magiceditor.core.piece_table import PieceTable
from magiceditor.core.syntax_limits import FULL_TEXT_MAX_BYTES
from magiceditor.services.compare_io import COMPARE_CAP_BYTES, read_compare_text


def test_full_text_huge_mode_requires_cap() -> None:
    doc = Document(buffer=PieceTable("x" * 100), huge_mode=True)
    with pytest.raises(ValueError):
        doc.full_text(max_bytes=None)
    clipped = doc.full_text(max_bytes=10)
    assert len(clipped) <= 10 + 20  # allow truncation marker


def test_compare_io_does_not_return_more_than_cap(tmp_path: Path) -> None:
    blob = tmp_path / "wide.bin"
    blob.write_bytes(b"Z" * (COMPARE_CAP_BYTES + 4096))
    text = read_compare_text(blob)
    assert len(text.encode("utf-8")) <= COMPARE_CAP_BYTES


def test_full_text_default_cap_constant() -> None:
    assert FULL_TEXT_MAX_BYTES < 50 * 1024 * 1024
