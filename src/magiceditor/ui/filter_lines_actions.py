"""Filter Lines action wiring (P1) — dialog + result tab.

Mixed into MainWindow (alongside DocumentToolsMixin) so ``main_window.py``
stays thin. The action is registered via ``window_chrome.ACTION_SPECS``
and enabled/disabled in ``DocumentToolsMixin._sync_doc_tool_actions``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from magiceditor.core.syntax_limits import syntax_enabled_for_size
from magiceditor.services.document import Document
from magiceditor.ui.filter_lines_dialog import FilterLinesDialog

if TYPE_CHECKING:
    from PyQt6.QtGui import QAction
    from PyQt6.QtWidgets import QWidget

    from magiceditor.i18n.translator import TranslatorManager
    from magiceditor.ui.editor_tab import EditorTab
    from magiceditor.ui.status_bar import EditorStatusBar

TITLE_PATTERN_MAX = 40


class FilterLinesMixin:
    """Expects to be mixed into MainWindow. Host attrs are typed."""

    _tr: TranslatorManager
    _actions: dict[str, QAction]
    _status: EditorStatusBar

    if TYPE_CHECKING:

        def current_tab(self) -> EditorTab | None: ...
        def _add_document(self, doc: Document, *, activate: bool = True) -> EditorTab: ...
        def _persist_session(self) -> None: ...

    def show_filter_lines(self: QWidget) -> None:
        tab = self.current_tab()  # type: ignore[attr-defined]
        if tab is None:
            return
        doc = tab.document
        dlg = FilterLinesDialog(
            line_count=doc.line_index().line_count,
            line_text=doc.line_text,
            tr=self._tr,
            parent=self,
        )
        dlg.result_ready.connect(self._open_filter_result)  # type: ignore[attr-defined]
        dlg.exec()

    def _open_filter_result(
        self, pattern: str, text: str, match_count: int, truncated: bool
    ) -> None:
        shown = pattern
        if len(shown) > TITLE_PATTERN_MAX:
            shown = shown[: TITLE_PATTERN_MAX - 1] + "…"
        doc = Document.from_text(text)
        doc.title = self._tr.t("filter.tab_title", "Filtro: {pattern}").format(pattern=shown)
        doc.modified = True
        # Piece table holds big results fine, but full-file lexers do not.
        doc.syntax_enabled = syntax_enabled_for_size(len(text.encode("utf-8")))
        tab = self._add_document(doc)  # type: ignore[attr-defined]
        if not doc.syntax_enabled:
            tab.editor.set_syntax_enabled(False)
        self._persist_session()  # type: ignore[attr-defined]
        key = "filter.truncated" if truncated else "filter.done"
        default = "{n} linha(s) extraída(s) (limite)." if truncated else "{n} linha(s) extraída(s)."
        self._status.showMessage(self._tr.t(key, default).format(n=match_count), 4000)
