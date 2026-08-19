"""Workspace path helpers extracted from the power mixin (J1.3)."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDockWidget, QFileDialog, QMessageBox, QPlainTextEdit

from magiceditor.services.theme_io import load_imported_theme, write_theme_bundle
from magiceditor.ui.compare_dialog import CompareDialog
from magiceditor.ui.nav_palette import split_view_text


def copy_path_text(path: str | Path | None) -> str:
    if path is None:
        return ""
    return str(Path(path))


def reveal_folder(path: str | Path | None) -> Path | None:
    if path is None:
        return None
    p = Path(path)
    if p.is_dir():
        return p
    if p.is_file():
        return p.parent
    return None


def run_compare_dialog(host) -> None:
    left, _ = QFileDialog.getOpenFileName(host, "Left file")
    if not left:
        return
    right, _ = QFileDialog.getOpenFileName(host, "Right file")
    if not right:
        return
    dlg = CompareDialog.from_paths(Path(left), Path(right), host)
    dlg.exec()


def run_toggle_split(host) -> None:
    tab = host._current_tab()
    if tab is None:
        return
    if host._split_secondary is not None:
        host.removeDockWidget(host._split_secondary)
        host._split_secondary = None
        return
    dock = QDockWidget(host._tr.t("split.title", "Split view"), host)
    view = QPlainTextEdit(dock)
    raw = tab.document.text() if len(tab.document.buffer) < 5_000_000 else ""
    view.setPlainText(split_view_text(len(tab.document.buffer), raw))
    view.setReadOnly(True)
    dock.setWidget(view)
    host.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
    host._split_secondary = dock


def run_export_theme(host) -> None:
    path, _ = QFileDialog.getSaveFileName(
        host,
        "Export theme",
        f"{host._session.theme}.json",
        "JSON (*.json)",
    )
    if not path:
        return
    write_theme_bundle(path, host._session.theme, host._session.icon_pack)


def run_import_theme(host) -> None:
    path, _ = QFileDialog.getOpenFileName(host, "Import theme", "", "JSON (*.json)")
    if not path:
        return
    try:
        theme = load_imported_theme(path)
    except (OSError, ValueError) as exc:
        QMessageBox.warning(host, "Import theme", str(exc))
        return
    if theme:
        host.apply_theme(theme, persist=True)
