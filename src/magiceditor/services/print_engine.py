"""Clean print / PDF export — force light printable styles."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QPageLayout, QPageSize, QTextDocument
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
from PyQt6.QtWidgets import QWidget


def printable_css() -> str:
    """CSS applied when exporting/printing (ignore dark theme)."""
    return """
    body {
      background: #ffffff;
      color: #000000;
      font-family: "Cascadia Code", Consolas, monospace;
      font-size: 10pt;
      line-height: 1.4;
      white-space: pre-wrap;
    }
    pre, code {
      background: #ffffff;
      color: #000000;
      font-family: "Cascadia Code", Consolas, monospace;
    }
    """


def _document_from_plain(text: str, title: str = "") -> QTextDocument:
    doc = QTextDocument()
    # Escape minimal HTML and wrap for clean print
    escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    html = (
        f"<html><head><style>{printable_css()}</style></head>"
        f"<body><pre>{escaped}</pre></body></html>"
    )
    doc.setHtml(html)
    if title:
        doc.setMetaInformation(QTextDocument.MetaInformation.DocumentTitle, title)
    return doc


def print_plain_text(text: str, parent: QWidget | None = None, title: str = "document") -> bool:
    """Show system print dialog and print with clean styles. Returns True if printed."""
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    printer.setPageOrientation(QPageLayout.Orientation.Portrait)
    dialog = QPrintDialog(printer, parent)
    dialog.setWindowTitle("Print")
    if dialog.exec() != QPrintDialog.DialogCode.Accepted:
        return False
    doc = _document_from_plain(text, title=title)
    doc.print(printer)
    return True


def export_pdf(
    text: str,
    path: str | Path,
    title: str = "document",
) -> Path:
    """Export plain text to a clean light PDF."""
    path = Path(path)
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(str(path))
    printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    doc = _document_from_plain(text, title=title)
    doc.print(printer)
    return path
