"""Print with in-app preview + PDF export (light printable styles).

Windows 11 native print dialog often shows “This app doesn't support print
preview” for Qt apps that only open ``QPrintDialog``. We use
``QPrintPreviewDialog`` so the user always gets a real preview before printing.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QMarginsF
from PyQt6.QtGui import QPageLayout, QPageSize, QTextDocument
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter, QPrintPreviewDialog
from PyQt6.QtWidgets import QWidget

# Cap print payload so huge-file buffers do not freeze the UI
_MAX_PRINT_CHARS = 1_500_000


def printable_css() -> str:
    """CSS applied when exporting/printing (ignore dark theme)."""
    return """
    body {
      background: #ffffff;
      color: #000000;
      font-family: "Cascadia Code", Consolas, "Courier New", monospace;
      font-size: 10pt;
      line-height: 1.45;
      white-space: pre-wrap;
      margin: 12mm;
    }
    pre, code {
      background: #ffffff;
      color: #000000;
      font-family: "Cascadia Code", Consolas, "Courier New", monospace;
      white-space: pre-wrap;
      word-wrap: break-word;
    }
    """


class _OfflineDocument(QTextDocument):
    """Printed HTML must not fetch images or stylesheets."""

    def loadResource(self, resource_type: int, name: object) -> None:
        del resource_type, name


def _document_from_plain(text: str, title: str = "") -> QTextDocument:
    doc = _OfflineDocument()
    body = text
    truncated = False
    if len(body) > _MAX_PRINT_CHARS:
        body = body[:_MAX_PRINT_CHARS]
        truncated = True
    escaped = body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    note = ""
    if truncated:
        note = (
            f"\n\n[… truncado para impressão: exibindo os primeiros "
            f"{_MAX_PRINT_CHARS:,} caracteres …]"
        )
    html = (
        f"<html><head><meta charset='utf-8'/>"
        f"<style>{printable_css()}</style></head>"
        f"<body><pre>{escaped}{note}</pre></body></html>"
    )
    doc.setHtml(html)
    if title:
        doc.setMetaInformation(QTextDocument.MetaInformation.DocumentTitle, title)
    return doc


def _configure_printer(printer: QPrinter) -> None:
    printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    printer.setPageOrientation(QPageLayout.Orientation.Portrait)
    printer.setPageMargins(QMarginsF(12, 12, 12, 12), QPageLayout.Unit.Millimeter)


def print_plain_text(
    text: str,
    parent: QWidget | None = None,
    title: str = "document",
    *,
    preview: bool = True,
) -> bool:
    """Print document. Default: in-app print **preview** dialog.

    Returns True if the user completed print (or closed preview after print).
    Set ``preview=False`` to open the system print dialog only.
    """
    # ScreenResolution: reliable preview; device DPI is used when printing
    printer = QPrinter(QPrinter.PrinterMode.ScreenResolution)
    _configure_printer(printer)
    doc = _document_from_plain(text, title=title)

    def _paint(p: QPrinter) -> None:
        doc.setPageSize(p.pageRect(QPrinter.Unit.Point).size())
        doc.print(p)

    if preview:
        dialog = QPrintPreviewDialog(printer, parent)
        dialog.setWindowTitle(f"Pré-visualizar impressão — {title}")
        dialog.resize(960, 720)
        dialog.paintRequested.connect(_paint)
        return dialog.exec() == QPrintPreviewDialog.DialogCode.Accepted

    dialog = QPrintDialog(printer, parent)
    dialog.setWindowTitle(f"Imprimir — {title}")
    if dialog.exec() != QPrintDialog.DialogCode.Accepted:
        return False
    _paint(printer)
    return True


def markdown_print_css() -> str:
    """Light print CSS for rendered Markdown. Body is not pre-wrap."""
    return """
    body {
      background: #ffffff;
      color: #111111;
      font-family: "Segoe UI", sans-serif;
      font-size: 11pt;
      line-height: 1.45;
      margin: 12mm;
    }
    h1, h2, h3, h4, h5, h6 {
      color: #111111;
      margin-top: 0.9em;
      margin-bottom: 0.3em;
    }
    p, li { margin: 0.35em 0; }
    a { color: #0645ad; }
    blockquote {
      margin-left: 0;
      padding-left: 10px;
      border-left: 3px solid #888888;
      color: #333333;
    }
    code, pre {
      font-family: Consolas, "Courier New", monospace;
      background: #f4f4f4;
      color: #111111;
    }
    pre { white-space: pre-wrap; padding: 8px; }
    table { border-collapse: collapse; margin: 8px 0; }
    th, td { border: 1px solid #cccccc; padding: 4px 8px; }
    """


def print_rich_html(
    html: str,
    parent: QWidget | None = None,
    title: str = "document",
    *,
    preview: bool = True,
) -> bool:
    """Print a sanitized HTML fragment (Markdown view) with a light stylesheet.

    CSS goes through ``setDefaultStyleSheet``. A ``<style>`` block in the HTML
    is painted as text by QTextDocument after tags are stripped.
    """
    printer = QPrinter(QPrinter.PrinterMode.ScreenResolution)
    _configure_printer(printer)
    doc = _OfflineDocument()
    body = html or ""
    if len(body) > _MAX_PRINT_CHARS:
        body = body[:_MAX_PRINT_CHARS] + "<p>[… truncado para impressão …]</p>"
    doc.setDefaultStyleSheet(markdown_print_css())
    doc.setHtml(body)
    if title:
        doc.setMetaInformation(QTextDocument.MetaInformation.DocumentTitle, title)

    def _paint(p: QPrinter) -> None:
        doc.setPageSize(p.pageRect(QPrinter.Unit.Point).size())
        doc.print(p)

    if preview:
        dialog = QPrintPreviewDialog(printer, parent)
        dialog.setWindowTitle(f"Pré-visualizar impressão — {title}")
        dialog.resize(960, 720)
        dialog.paintRequested.connect(_paint)
        return dialog.exec() == QPrintPreviewDialog.DialogCode.Accepted

    dialog = QPrintDialog(printer, parent)
    dialog.setWindowTitle(f"Imprimir — {title}")
    if dialog.exec() != QPrintDialog.DialogCode.Accepted:
        return False
    _paint(printer)
    return True


def print_preview_plain_text(
    text: str,
    parent: QWidget | None = None,
    title: str = "document",
) -> bool:
    """Alias: always open the in-app print preview."""
    return print_plain_text(text, parent=parent, title=title, preview=True)


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
    _configure_printer(printer)
    doc = _document_from_plain(text, title=title)
    doc.setPageSize(printer.pageRect(QPrinter.Unit.Point).size())
    doc.print(printer)
    return path
