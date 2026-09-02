"""Document-tools mixin: case/encode transforms, extra line ops, insert
date/time, Save All, Always-on-top, per-tab read-only, checksum and stats.

Mixed into MainWindow (alongside PowerFeaturesMixin) to keep
``main_window.py`` thin — see ``ui/AGENTS.md``. Slots are wired through
``window_chrome.ACTION_SPECS`` like every other action.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox

from magiceditor.core.line_ops import (
    remove_consecutive_duplicates,
    remove_duplicate_lines,
    reverse_lines,
    sort_lines_by_length,
)
from magiceditor.core.syntax_limits import FULL_TEXT_MAX_BYTES
from magiceditor.core.text_stats import stats_for_text
from magiceditor.core.text_transform import (
    base64_decode,
    base64_encode,
    invert_case,
    to_lower,
    to_sentence_case,
    to_title_case,
    to_upper,
    url_decode,
    url_encode,
)
from magiceditor.services.document_io import save_document
from magiceditor.ui.convert_actions import transform_selection

if TYPE_CHECKING:
    from PyQt6.QtGui import QAction

    from magiceditor.i18n.translator import TranslatorManager
    from magiceditor.ui.editor_tab import EditorTab
    from magiceditor.ui.status_bar import EditorStatusBar
    from magiceditor.ui.tab_manager import TabManager

CONVERT_ACTION_KEYS = (
    "action.case_upper",
    "action.case_lower",
    "action.case_title",
    "action.case_sentence",
    "action.case_invert",
    "action.base64_encode",
    "action.base64_decode",
    "action.url_encode",
    "action.url_decode",
)
LINE_OP_EXTRA_KEYS = (
    "action.sort_by_length",
    "action.reverse_lines",
    "action.remove_duplicate_lines",
    "action.remove_consecutive_duplicates",
)
INSERT_DT_KEYS = (
    "action.insert_datetime_iso",
    "action.insert_date_short",
    "action.insert_datetime_local",
    "action.insert_timestamp",
)

# Visual marker appended to the tab/window title of a read-only document.
READ_ONLY_SUFFIX = " 🔒"


class DocumentToolsMixin:
    """Expects to be mixed into MainWindow. Host attrs are typed."""

    _tr: TranslatorManager
    tabs: TabManager
    _status: EditorStatusBar
    _actions: dict[str, QAction]

    if TYPE_CHECKING:

        def current_tab(self) -> EditorTab | None: ...
        def _persist_session(self) -> None: ...
        def _refresh_tab_titles(self) -> None: ...
        def _apply_line_transform(self, transform: Any) -> None: ...
        def windowFlags(self) -> Any: ...
        def setWindowFlag(self, flag: Any, on: bool = True) -> None: ...
        def isMaximized(self) -> bool: ...
        def show(self) -> None: ...
        def showMaximized(self) -> None: ...

    def _init_document_tools(self) -> None:
        """Lazy enable/disable sync when Edit/Tools menus open."""
        for menu in (getattr(self, "_menu_edit", None), getattr(self, "_menu_tools", None)):
            if menu is not None:
                menu.aboutToShow.connect(self.refresh_tool_action_states)

    def refresh_tool_action_states(self) -> None:
        self._sync_doc_tool_actions(self.current_tab())

    def _sync_doc_tool_actions(self, tab: EditorTab | None) -> None:
        """Enable/disable + checked state for the document-tool actions."""
        acts = self._actions
        has_tab = tab is not None
        editor = getattr(tab, "editor", None)
        read_only = bool(editor is not None and editor.is_read_only())
        has_sel = bool(editor is not None and editor.has_selection())
        for key in CONVERT_ACTION_KEYS:
            acts[key].setEnabled(has_sel and not read_only)
        for key in (*LINE_OP_EXTRA_KEYS, *INSERT_DT_KEYS):
            acts[key].setEnabled(has_tab and not read_only)
        acts["action.toggle_read_only"].setEnabled(has_tab)
        if has_tab:
            acts["action.toggle_read_only"].setChecked(read_only)
        path = getattr(getattr(tab, "document", None), "path", None)
        acts["action.file_checksum"].setEnabled(path is not None)
        acts["action.doc_stats"].setEnabled(has_tab)
        on_top = bool(self.windowFlags() & Qt.WindowType.WindowStaysOnTopHint)
        acts["action.always_on_top"].setChecked(on_top)

    # --- case / Base64 / URL (selection) -------------------------------

    def _apply_selection_transform(self, transform: Any) -> None:
        tab = self.current_tab()
        if tab is None:
            return
        transform_selection(tab.editor, transform)

    def case_upper_current(self) -> None:
        self._apply_selection_transform(to_upper)

    def case_lower_current(self) -> None:
        self._apply_selection_transform(to_lower)

    def case_title_current(self) -> None:
        self._apply_selection_transform(to_title_case)

    def case_sentence_current(self) -> None:
        self._apply_selection_transform(to_sentence_case)

    def case_invert_current(self) -> None:
        self._apply_selection_transform(invert_case)

    def base64_encode_current(self) -> None:
        self._apply_selection_transform(base64_encode)

    def base64_decode_current(self) -> None:
        tab = self.current_tab()
        if tab is None:
            return
        try:
            transform_selection(tab.editor, base64_decode)
        except ValueError:
            QMessageBox.warning(
                self,  # type: ignore[arg-type]
                self._tr.t("app.name", "MagicEditor"),
                self._tr.t("msg.invalid_base64", "A seleção não é Base64 válido."),
            )

    def url_encode_current(self) -> None:
        self._apply_selection_transform(url_encode)

    def url_decode_current(self) -> None:
        self._apply_selection_transform(url_decode)

    # --- extra line ops --------------------------------------------------

    def _apply_line_op_guarded(self, op: Any) -> None:
        tab = self.current_tab()
        if tab is None or tab.editor.is_read_only():
            return
        self._apply_line_transform(op)

    def sort_by_length_current(self) -> None:
        self._apply_line_op_guarded(sort_lines_by_length)

    def reverse_lines_current(self) -> None:
        self._apply_line_op_guarded(reverse_lines)

    def remove_duplicate_lines_current(self) -> None:
        self._apply_line_op_guarded(remove_duplicate_lines)

    def remove_consecutive_duplicates_current(self) -> None:
        self._apply_line_op_guarded(remove_consecutive_duplicates)

    # --- insert date/time -------------------------------------------------

    def _insert_text_at_cursor(self, text: str) -> None:
        tab = self.current_tab()
        if tab is None or tab.editor.is_read_only():
            return
        tab.editor.insert(text)

    def insert_datetime_iso(self) -> None:
        self._insert_text_at_cursor(datetime.now().strftime("%Y-%m-%d %H:%M"))

    def insert_date_short(self) -> None:
        self._insert_text_at_cursor(datetime.now().strftime("%x"))

    def insert_datetime_local(self) -> None:
        self._insert_text_at_cursor(datetime.now().strftime("%x %X"))

    def insert_timestamp(self) -> None:
        self._insert_text_at_cursor(str(int(time.time())))

    # --- file / window ----------------------------------------------------

    def save_all(self) -> None:
        """Save every dirty tab that has a path; untitled stay dirty."""
        saved = 0
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            doc = getattr(w, "document", None)
            if doc is None or doc.path is None or not doc.modified:
                continue
            try:
                save_document(doc)
            except OSError:
                continue
            doc.modified = False
            signal = getattr(w, "modification_changed", None)
            if signal is not None:
                signal.emit()
            saved += 1
        if saved:
            self._refresh_tab_titles()
            self._persist_session()
        self._status.showMessage(
            self._tr.t("status.saved_count", "{n} arquivo(s) salvo(s)").format(n=saved),
            3000,
        )

    def toggle_always_on_top(self) -> None:
        on = not bool(self.windowFlags() & Qt.WindowType.WindowStaysOnTopHint)
        was_max = self.isMaximized()
        # The flag only takes effect after the window is re-shown; keep
        # the geometry and the maximized state intact.
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, on)
        if was_max:
            self.showMaximized()
        else:
            self.show()
        self._actions["action.always_on_top"].setChecked(on)

    def toggle_read_only(self) -> None:
        tab = self.current_tab()
        if tab is None:
            return
        new = not tab.editor.is_read_only()
        tab.editor.set_read_only(new)
        self._actions["action.toggle_read_only"].setChecked(new)
        self._refresh_tab_titles()
        key = "status.read_only_on" if new else "status.read_only_off"
        default = "Aba somente leitura" if new else "Edição habilitada"
        self._status.showMessage(self._tr.t(key, default), 2500)
        self._sync_doc_tool_actions(tab)

    # --- tools dialogs -----------------------------------------------------

    def show_checksum_dialog(self) -> None:
        tab = self.current_tab()
        if tab is None or tab.document.path is None:
            return
        from magiceditor.ui.checksum_dialog import ChecksumDialog

        dlg = ChecksumDialog(
            tab.document.path,
            dirty=tab.document.modified,
            tr=self._tr,
            parent=self,  # type: ignore[arg-type]
        )
        dlg.exec()

    def show_stats_dialog(self) -> None:
        tab = self.current_tab()
        if tab is None:
            return
        doc = tab.document
        partial_bytes: int | None = None
        if doc.huge_mode:
            # Never materialize the full buffer: stats over the capped export.
            text = doc.full_text(max_bytes=FULL_TEXT_MAX_BYTES)
            if len(doc.buffer) > FULL_TEXT_MAX_BYTES:
                partial_bytes = FULL_TEXT_MAX_BYTES
        else:
            text = doc.full_text(max_bytes=None)
        stats = stats_for_text(text)
        from magiceditor.ui.stats_dialog import StatsDialog

        dlg = StatsDialog(
            stats,
            encoding=doc.encoding,
            eol=doc.eol,
            partial_bytes=partial_bytes,
            tr=self._tr,
            parent=self,  # type: ignore[arg-type]
        )
        dlg.exec()
