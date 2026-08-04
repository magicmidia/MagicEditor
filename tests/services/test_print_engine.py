"""Print engine helpers (requires QApplication for QTextDocument)."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication  # noqa: E402

from magiceditor.services.print_engine import (  # noqa: E402
    _document_from_plain,
    export_pdf,
    printable_css,
)


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_printable_css_is_light() -> None:
    css = printable_css()
    assert "#ffffff" in css
    assert "font-family" in css


def test_document_from_plain_escapes_html(qapp) -> None:
    doc = _document_from_plain("a < b & c > d", title="t")
    html = doc.toHtml()
    assert "&lt;" in html or "&#" in html
    assert "&amp;" in html or "&#" in html


def test_export_pdf_writes_file(qapp) -> None:
    # Write under repo to avoid Windows Temp ACL issues
    base = Path(__file__).resolve().parents[2] / "tmp"
    base.mkdir(exist_ok=True)
    out = base / "test_print_sample.pdf"
    try:
        path = export_pdf("Hello MagicEditor\nLine 2", out, title="sample")
        assert path.is_file()
        assert path.stat().st_size > 100
    finally:
        if out.is_file():
            out.unlink(missing_ok=True)
