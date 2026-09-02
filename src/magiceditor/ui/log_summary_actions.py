"""Log Summary action wiring (P6) — dialog + next-level navigation.

Mixed into MainWindow (alongside FilterLinesMixin) so ``main_window.py``
stays thin. The action is registered via ``window_chrome.ACTION_SPECS``
and enabled/disabled in ``DocumentToolsMixin._sync_doc_tool_actions``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from magiceditor.core.log_levels import next_line_with_level
from magiceditor.ui.log_summary_dialog import LogSummaryDialog

if TYPE_CHECKING:
    from PyQt6.QtGui import QAction
    from PyQt6.QtWidgets import QWidget

    from magiceditor.i18n.translator import TranslatorManager
    from magiceditor.ui.editor_tab import EditorTab
    from magiceditor.ui.status_bar import EditorStatusBar


class LogSummaryMixin:
    """Expects to be mixed into MainWindow. Host attrs are typed."""

    _tr: TranslatorManager
    _actions: dict[str, QAction]
    _status: EditorStatusBar

    if TYPE_CHECKING:

        def current_tab(self) -> EditorTab | None: ...

    def show_log_summary(self: QWidget) -> None:
        tab = self.current_tab()  # type: ignore[attr-defined]
        if tab is None:
            return
        doc = tab.document
        dlg = LogSummaryDialog(
            line_count=doc.line_index().line_count,
            line_text=doc.line_text,
            tr=self._tr,
            parent=self,
        )
        dlg.goto_level_requested.connect(lambda level, t=tab: self._goto_log_level(t, level))
        dlg.exec()

    def _goto_log_level(self, tab: EditorTab, level: str) -> None:
        doc = tab.document
        total = doc.line_index().line_count
        current_line, _ = tab.editor.cursor_line_col()  # 1-based
        target = next_line_with_level(total, doc.line_text, level, current_line - 1)
        if target is None:
            self._status.showMessage(
                self._tr.t("log_summary.none", "Nenhuma linha com nível {level}.").format(
                    level=level.upper()
                ),
                3000,
            )
            return
        tab.goto_line(target + 1, 1)
