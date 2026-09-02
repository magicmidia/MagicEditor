"""Document statistics dialog (Tools menu).

Pure presentation of a ``core.text_stats.TextStats`` snapshot plus the
tab's encoding/EOL. For huge files the caller passes ``partial_bytes``
and the dialog marks the values as partial (first N MB only).
"""

from __future__ import annotations

from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from magiceditor.core.text_stats import TextStats


class StatsDialog(QDialog):
    """Read-only stats sheet: chars, words, lines + encoding/EOL."""

    def __init__(
        self,
        stats: TextStats,
        *,
        encoding: str,
        eol: str,
        partial_bytes: int | None = None,
        tr: QObject | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._tr = tr
        self.setWindowTitle(self._t("stats.title", "Estatísticas do documento"))
        self.setModal(True)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        rows = (
            ("stats.chars", "Caracteres:", stats.chars),
            ("stats.chars_no_spaces", "Caracteres (sem espaços):", stats.chars_no_spaces),
            ("stats.words", "Palavras:", stats.words),
            ("stats.lines", "Linhas:", stats.lines),
            ("stats.non_empty_lines", "Linhas não vazias:", stats.non_empty_lines),
        )
        for key, default, value in rows:
            form.addRow(self._t(key, default), QLabel(f"{value:,}"))
        form.addRow(self._t("stats.encoding", "Codificação:"), QLabel(encoding.upper()))
        form.addRow(self._t("stats.eol", "Fim de linha:"), QLabel(eol))
        layout.addLayout(form)

        if partial_bytes is not None:
            mb = max(1, partial_bytes // (1024 * 1024))
            note = QLabel(self._t("stats.partial", "Parcial (primeiros {mb} MB)").format(mb=mb))
            note.setObjectName("statsPartialNote")
            layout.addWidget(note)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _t(self, key: str, default: str) -> str:
        tr = self._tr
        if tr is not None and hasattr(tr, "t"):
            return tr.t(key, default)  # type: ignore[no-any-return,union-attr]
        return default
