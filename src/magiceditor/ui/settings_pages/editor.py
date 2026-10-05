"""Editor settings page (J1.4)."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from magiceditor.services.settings import SessionState
from magiceditor.ui.settings_pages.common import Translate, wrap_scroll

PAGE_ID = "editor"


class EditorPage(QWidget):
    def __init__(self, state: SessionState, t: Translate, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(22, 20, 22, 20)
        lay.setSpacing(14)

        g = QGroupBox(t("settings.editor_group", "Edição"), page)
        form = QFormLayout(g)
        form.setSpacing(8)
        form.setContentsMargins(12, 16, 12, 12)

        self.font_size_spin = QSpinBox(g)
        self.font_size_spin.setRange(8, 48)
        self.font_size_spin.setValue(int(state.font_size or 12))
        self.font_size_spin.setSuffix(" pt")
        form.addRow(t("settings.font_size", "Tamanho da fonte"), self.font_size_spin)

        self.tab_width_spin = QSpinBox(g)
        self.tab_width_spin.setRange(2, 8)
        self.tab_width_spin.setValue(int(state.tab_width or 4))
        form.addRow(t("settings.tab_width", "Largura da tabulação"), self.tab_width_spin)

        self.indent_spaces_box = QCheckBox(
            t("settings.indent_spaces", "Indentar com espaços (em vez de tab)"), g
        )
        self.indent_spaces_box.setChecked(state.indent_with_spaces)
        form.addRow(self.indent_spaces_box)

        self.caret_width_spin = QSpinBox(g)
        self.caret_width_spin.setRange(1, 4)
        self.caret_width_spin.setValue(int(state.caret_width or 1))
        form.addRow(t("settings.caret_width", "Espessura do cursor"), self.caret_width_spin)

        self.word_wrap_box = QCheckBox(t("settings.word_wrap", "Quebra de linha"), g)
        self.word_wrap_box.setChecked(state.word_wrap)
        form.addRow(self.word_wrap_box)

        self.line_numbers_box = QCheckBox(t("settings.line_numbers", "Números de linha"), g)
        self.line_numbers_box.setChecked(state.line_numbers)
        form.addRow(self.line_numbers_box)

        self.highlight_line_box = QCheckBox(t("settings.highlight_line", "Destacar linha atual"), g)
        self.highlight_line_box.setChecked(state.highlight_current_line)
        form.addRow(self.highlight_line_box)

        self.show_ws_box = QCheckBox(t("settings.show_whitespace", "Mostrar espaços e tabs"), g)
        self.show_ws_box.setChecked(bool(state.show_whitespace))
        form.addRow(self.show_ws_box)

        self.brace_box = QCheckBox(t("settings.brace_match", "Destacar par de chaves/colchetes"), g)
        self.brace_box.setChecked(bool(state.brace_match))
        form.addRow(self.brace_box)

        self.syntax_box = QCheckBox(t("settings.syntax_highlight", "Realce de sintaxe"), g)
        self.syntax_box.setChecked(bool(state.syntax_highlight))
        form.addRow(self.syntax_box)

        self.word_completion_box = QCheckBox(
            t("settings.word_completion", "Completar palavras do documento"), g
        )
        self.word_completion_box.setChecked(bool(state.word_completion))
        form.addRow(self.word_completion_box)

        self.line_spacing_spin = QSpinBox(g)
        self.line_spacing_spin.setRange(0, 16)
        self.line_spacing_spin.setValue(int(state.line_spacing or 0))
        self.line_spacing_spin.setSuffix(" px")
        form.addRow(t("settings.line_spacing", "Espaço extra entre linhas"), self.line_spacing_spin)

        self.right_margin_spin = QSpinBox(g)
        self.right_margin_spin.setRange(0, 240)
        self.right_margin_spin.setValue(int(state.right_margin or 0))
        form.addRow(
            t("settings.right_margin", "Margem direita (0 desliga)"),
            self.right_margin_spin,
        )

        self.indent_guides_box = QCheckBox(t("settings.indent_guides", "Guias de indentação"), g)
        self.indent_guides_box.setChecked(bool(state.indent_guides))
        form.addRow(self.indent_guides_box)

        self.auto_close_box = QCheckBox(
            t("settings.auto_close_brackets", "Fechar parênteses, colchetes e aspas"), g
        )
        self.auto_close_box.setChecked(bool(state.auto_close_brackets))
        form.addRow(self.auto_close_box)

        self.highlight_occurrences_box = QCheckBox(
            t("settings.highlight_occurrences", "Destacar outras ocorrências da palavra"), g
        )
        self.highlight_occurrences_box.setChecked(bool(state.highlight_occurrences))
        form.addRow(self.highlight_occurrences_box)

        self.wheel_zoom_box = QCheckBox(
            t("settings.wheel_zoom", "Ctrl + roda do mouse altera o zoom"), g
        )
        self.wheel_zoom_box.setChecked(bool(state.wheel_zoom))
        form.addRow(self.wheel_zoom_box)
        lay.addWidget(g)

        rec = QGroupBox(t("settings.recovery_group", "Recuperação"), page)
        rec_form = QFormLayout(rec)
        rec_form.setSpacing(8)
        rec_form.setContentsMargins(12, 16, 12, 12)
        self.recovery_interval_spin = QSpinBox(rec)
        self.recovery_interval_spin.setRange(2, 120)
        self.recovery_interval_spin.setValue(int(state.recovery_interval_sec or 8))
        self.recovery_interval_spin.setSuffix(" s")
        rec_form.addRow(
            t("settings.recovery_interval", "Intervalo da recuperação"),
            self.recovery_interval_spin,
        )
        hint = QLabel(
            t(
                "settings.recovery_hint",
                "Guarda o texto das abas na recuperação. Não grava por cima do arquivo.",
            ),
            rec,
        )
        hint.setWordWrap(True)
        rec_form.addRow(hint)
        lay.addWidget(rec)

        save_g = QGroupBox(t("settings.save_group", "Ao salvar"), page)
        save_form = QFormLayout(save_g)
        save_form.setSpacing(8)
        save_form.setContentsMargins(12, 16, 12, 12)
        self.trim_save_box = QCheckBox(
            t("settings.trim_on_save", "Remover espaços no fim das linhas"), save_g
        )
        self.trim_save_box.setChecked(bool(state.trim_trailing_on_save))
        save_form.addRow(self.trim_save_box)
        self.final_nl_box = QCheckBox(
            t("settings.final_newline", "Garantir quebra de linha final"), save_g
        )
        self.final_nl_box.setChecked(bool(state.insert_final_newline))
        save_form.addRow(self.final_nl_box)
        lay.addWidget(save_g)

        a11y = QGroupBox(t("settings.a11y_group", "Acessibilidade"), page)
        a11y_form = QFormLayout(a11y)
        a11y_form.setContentsMargins(12, 16, 12, 12)
        self.high_contrast_box = QCheckBox(t("settings.high_contrast", "Alto contraste"), a11y)
        self.high_contrast_box.setChecked(bool(state.high_contrast))
        a11y_form.addRow(self.high_contrast_box)
        lay.addWidget(a11y)
        lay.addStretch(1)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(wrap_scroll(self, page))

    def apply(self, state: SessionState) -> None:
        state.font_size = int(self.font_size_spin.value())
        state.tab_width = int(self.tab_width_spin.value())
        state.indent_with_spaces = self.indent_spaces_box.isChecked()
        state.caret_width = int(self.caret_width_spin.value())
        state.word_wrap = self.word_wrap_box.isChecked()
        state.line_numbers = self.line_numbers_box.isChecked()
        state.highlight_current_line = self.highlight_line_box.isChecked()
        state.show_whitespace = self.show_ws_box.isChecked()
        state.brace_match = self.brace_box.isChecked()
        state.syntax_highlight = self.syntax_box.isChecked()
        state.word_completion = self.word_completion_box.isChecked()
        state.line_spacing = int(self.line_spacing_spin.value())
        state.right_margin = int(self.right_margin_spin.value())
        state.indent_guides = self.indent_guides_box.isChecked()
        state.auto_close_brackets = self.auto_close_box.isChecked()
        state.highlight_occurrences = self.highlight_occurrences_box.isChecked()
        state.wheel_zoom = self.wheel_zoom_box.isChecked()
        state.recovery_interval_sec = int(self.recovery_interval_spin.value())
        state.trim_trailing_on_save = self.trim_save_box.isChecked()
        state.insert_final_newline = self.final_nl_box.isChecked()
        state.high_contrast = self.high_contrast_box.isChecked()
