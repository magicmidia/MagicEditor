"""Print / PDF wiring extracted from MainWindow (J1.2)."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QFileDialog, QMessageBox

from magiceditor.services.print_engine import export_pdf, print_plain_text


def print_current(window) -> None:
    tab = window.current_tab()
    if tab is None:
        return
    tab.sync_document_from_editor()
    try:
        text = tab.export_text()
    except Exception as exc:
        QMessageBox.critical(window, "MagicEditor", str(exc))
        return
    if not text.strip():
        QMessageBox.information(
            window,
            window._tr.t("app.name", "MagicEditor"),
            window._tr.t(
                "msg.print_empty",
                "Não há conteúdo para imprimir neste documento.",
            ),
        )
        return
    ok = print_plain_text(
        text,
        parent=window,
        title=tab.document.title,
        preview=True,
    )
    if ok:
        window._status.showMessage(
            window._tr.t("msg.printed", "Enviado para impressão"),
            2500,
        )


def export_pdf_current(window) -> None:
    tab = window.current_tab()
    if tab is None:
        return
    tab.sync_document_from_editor()
    default = Path.home() / f"{Path(tab.document.title).stem or 'document'}.pdf"
    path, _ = QFileDialog.getSaveFileName(
        window,
        window._tr.t("action.export_pdf", "Export PDF…"),
        str(default),
        "PDF (*.pdf)",
    )
    if not path:
        return
    try:
        export_pdf(tab.export_text(), path, title=tab.document.title)
    except OSError as exc:
        QMessageBox.critical(window, "MagicEditor", str(exc))
        return
    window._status.showMessage(f"PDF saved: {Path(path).name}", 3500)
