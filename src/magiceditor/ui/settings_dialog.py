"""Settings dialog — deep multi-pane preferences."""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QSlider,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from magiceditor.services.settings import SessionState
from magiceditor.themes.manager import NATIVE_THEMES
from magiceditor.ui.icons import ICON_PACKS


class SettingsDialog(QDialog):
    """Multi-pane settings: Geral · Editor · Ortografia · Design · Gráficos · Abas · Desempenho."""

    def __init__(
        self,
        state: SessionState,
        parent: QWidget | None = None,
        *,
        tr: Any | None = None,
        languages: list[str] | None = None,
    ) -> None:
        super().__init__(parent)
        self._tr = tr
        self.setModal(True)
        self.setMinimumSize(680, 520)
        self.resize(760, 580)
        self.setObjectName("settingsDialog")

        def t(key: str, default: str) -> str:
            if self._tr is not None:
                return self._tr.t(key, default)
            return default

        self._t = t
        self.setWindowTitle(t("settings.title", "Configurações"))

        self.nav = QListWidget(self)
        self.nav.setObjectName("settingsNav")
        self.nav.setFixedWidth(176)
        self.nav.setSpacing(2)
        subjects = [
            ("general", t("settings.tab.general", "Geral")),
            ("editor", t("settings.tab.editor", "Editor")),
            ("spell", t("settings.tab.spell", "Ortografia")),
            ("design", t("settings.tab.design", "Design")),
            ("graphics", t("settings.tab.graphics", "Gráficos")),
            ("tabs", t("settings.tab.tabs", "Abas")),
            ("performance", t("settings.tab.performance", "Desempenho")),
        ]
        for _sid, label in subjects:
            self.nav.addItem(QListWidgetItem(label))

        self.stack = QStackedWidget(self)
        self.stack.addWidget(self._page_general(state))
        self.stack.addWidget(self._page_editor(state))
        self.stack.addWidget(self._page_spell(state))
        self.stack.addWidget(self._page_design(state))
        self.stack.addWidget(self._page_graphics(state))
        self.stack.addWidget(self._page_tabs(state))
        self.stack.addWidget(self._page_performance(state))

        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.nav.setCurrentRow(0)

        body = QHBoxLayout()
        body.setSpacing(0)
        body.setContentsMargins(0, 0, 0, 0)
        body.addWidget(self.nav)
        sep = QFrame(self)
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setObjectName("settingsSep")
        body.addWidget(sep)
        body.addWidget(self.stack, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        cancel_btn = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if ok_btn is not None:
            ok_btn.setText(t("dialog.ok", "OK"))
        if cancel_btn is not None:
            cancel_btn.setText(t("dialog.cancel", "Cancelar"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 10)
        root.setSpacing(10)
        root.addLayout(body, 1)
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(14, 0, 14, 0)
        btn_row.addStretch(1)
        btn_row.addWidget(buttons)
        root.addLayout(btn_row)

        QShortcut(QKeySequence("Esc"), self, activated=self.reject)
        self._sync_gpu_deps(self.gpu_box.isChecked())

        langs = languages or ["pt_BR", "en_US", "es_ES"]
        lang_labels = {
            "pt_BR": t("lang.pt_BR", "Português (Brasil)"),
            "en_US": t("lang.en_US", "English (US)"),
            "es_ES": t("lang.es_ES", "Español"),
        }
        self.lang_box.clear()
        for code in langs:
            self.lang_box.addItem(lang_labels.get(code, code), code)
        idx = self.lang_box.findData(state.language or "pt_BR")
        self.lang_box.setCurrentIndex(max(0, idx))

    # --- helpers ------------------------------------------------------

    def _wrap_scroll(self, inner: QWidget) -> QWidget:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(inner)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        return scroll

    def _hint(self, text: str, parent: QWidget) -> QLabel:
        tip = QLabel(text, parent)
        tip.setWordWrap(True)
        tip.setObjectName("findDialogStatus")
        return tip

    # --- pages --------------------------------------------------------

    def _page_general(self, state: SessionState) -> QWidget:
        t = self._t
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        g = QGroupBox(t("settings.general_group", "Geral"), page)
        form = QFormLayout(g)
        form.setSpacing(8)
        form.setContentsMargins(12, 16, 12, 12)

        self.lang_box = QComboBox(g)
        form.addRow(t("settings.language", "Idioma"), self.lang_box)

        self.restore_session_box = QCheckBox(
            t("settings.restore_session", "Restaurar abas e rascunhos ao iniciar"), g
        )
        self.restore_session_box.setChecked(state.restore_session)
        form.addRow(self.restore_session_box)

        self.show_toolbar_box = QCheckBox(
            t("settings.show_toolbar", "Mostrar barra de ferramentas"), g
        )
        self.show_toolbar_box.setChecked(state.show_toolbar)
        form.addRow(self.show_toolbar_box)

        self.show_status_box = QCheckBox(
            t("settings.show_status_bar", "Mostrar barra de status"), g
        )
        self.show_status_box.setChecked(state.show_status_bar)
        form.addRow(self.show_status_box)

        self.recent_max_spin = QSpinBox(g)
        self.recent_max_spin.setRange(5, 50)
        self.recent_max_spin.setValue(int(getattr(state, "recent_files_max", 15) or 15))
        form.addRow(
            t("settings.recent_max", "Máx. arquivos recentes"),
            self.recent_max_spin,
        )

        self.context_menu_box = QCheckBox(
            t("settings.editor_context_menu", "Menu de contexto no editor (botão direito)"),
            g,
        )
        self.context_menu_box.setChecked(bool(getattr(state, "editor_context_menu", True)))
        form.addRow(self.context_menu_box)

        self.splash_box = QCheckBox(
            t(
                "settings.show_splash",
                "Mostrar tela inicial (splash) ao abrir — mínimo 5 segundos",
            ),
            g,
        )
        self.splash_box.setChecked(bool(getattr(state, "show_splash", True)))
        form.addRow(self.splash_box)

        lay.addWidget(g)
        lay.addWidget(
            self._hint(
                t(
                    "settings.general_hint",
                    "Idioma e restauração de sessão aplicam-se ao confirmar.",
                ),
                page,
            )
        )
        lay.addStretch(1)
        return self._wrap_scroll(page)

    def _page_editor(self, state: SessionState) -> QWidget:
        t = self._t
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        g = QGroupBox(t("settings.editor_group", "Edição"), page)
        form = QFormLayout(g)
        form.setSpacing(8)
        form.setContentsMargins(12, 16, 12, 12)

        self.font_size_spin = QSpinBox(g)
        self.font_size_spin.setRange(8, 48)
        self.font_size_spin.setValue(int(getattr(state, "font_size", 12) or 12))
        self.font_size_spin.setSuffix(" pt")
        form.addRow(t("settings.font_size", "Tamanho da fonte"), self.font_size_spin)

        self.tab_width_spin = QSpinBox(g)
        self.tab_width_spin.setRange(2, 8)
        self.tab_width_spin.setValue(int(getattr(state, "tab_width", 4) or 4))
        form.addRow(t("settings.tab_width", "Largura da tabulação"), self.tab_width_spin)

        self.indent_spaces_box = QCheckBox(
            t("settings.indent_spaces", "Indentar com espaços (em vez de tab)"), g
        )
        self.indent_spaces_box.setChecked(state.indent_with_spaces)
        form.addRow(self.indent_spaces_box)

        self.caret_width_spin = QSpinBox(g)
        self.caret_width_spin.setRange(1, 4)
        self.caret_width_spin.setValue(int(getattr(state, "caret_width", 1) or 1))
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
        self.show_ws_box.setChecked(bool(getattr(state, "show_whitespace", False)))
        form.addRow(self.show_ws_box)

        self.brace_box = QCheckBox(t("settings.brace_match", "Destacar par de chaves/colchetes"), g)
        self.brace_box.setChecked(bool(getattr(state, "brace_match", True)))
        form.addRow(self.brace_box)

        self.syntax_box = QCheckBox(t("settings.syntax_highlight", "Realce de sintaxe"), g)
        self.syntax_box.setChecked(bool(getattr(state, "syntax_highlight", True)))
        form.addRow(self.syntax_box)

        self.word_completion_box = QCheckBox(
            t("settings.word_completion", "Completar palavras do documento"), g
        )
        self.word_completion_box.setChecked(bool(getattr(state, "word_completion", False)))
        form.addRow(self.word_completion_box)

        lay.addWidget(g)

        save_g = QGroupBox(t("settings.save_group", "Ao salvar"), page)
        save_form = QFormLayout(save_g)
        save_form.setSpacing(8)
        save_form.setContentsMargins(12, 16, 12, 12)

        self.trim_save_box = QCheckBox(
            t("settings.trim_on_save", "Remover espaços no fim das linhas"), save_g
        )
        self.trim_save_box.setChecked(bool(getattr(state, "trim_trailing_on_save", False)))
        save_form.addRow(self.trim_save_box)

        self.final_nl_box = QCheckBox(
            t("settings.final_newline", "Garantir quebra de linha final"), save_g
        )
        self.final_nl_box.setChecked(bool(getattr(state, "insert_final_newline", False)))
        save_form.addRow(self.final_nl_box)

        lay.addWidget(save_g)

        a11y = QGroupBox(t("settings.a11y_group", "Acessibilidade"), page)
        a11y_form = QFormLayout(a11y)
        a11y_form.setContentsMargins(12, 16, 12, 12)
        self.high_contrast_box = QCheckBox(t("settings.high_contrast", "Alto contraste"), a11y)
        self.high_contrast_box.setChecked(bool(getattr(state, "high_contrast", False)))
        a11y_form.addRow(self.high_contrast_box)
        lay.addWidget(a11y)
        lay.addStretch(1)
        return self._wrap_scroll(page)

    def _page_spell(self, state: SessionState) -> QWidget:
        t = self._t
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        g = QGroupBox(t("settings.spell_group", "Correção ortográfica"), page)
        form = QFormLayout(g)
        form.setSpacing(8)
        form.setContentsMargins(12, 16, 12, 12)

        self.spell_box = QCheckBox(t("settings.spell_check", "Ativar ortografia"), g)
        self.spell_box.setChecked(bool(getattr(state, "spell_check", True)))
        form.addRow(self.spell_box)

        self.spell_all_box = QCheckBox(
            t(
                "settings.spell_all_files",
                "Aplicar a todos os tipos de arquivo (não só texto/markdown)",
            ),
            g,
        )
        self.spell_all_box.setChecked(getattr(state, "spell_force", None) is True)
        form.addRow(self.spell_all_box)

        self.spell_lang_box = QComboBox(g)
        for code, label in (
            ("pt_BR", "Português (Brasil)"),
            ("en_US", "English (US)"),
            ("es_ES", "Español"),
        ):
            self.spell_lang_box.addItem(label, code)
        sidx = self.spell_lang_box.findData(getattr(state, "spell_language", None) or "pt_BR")
        self.spell_lang_box.setCurrentIndex(max(0, sidx))
        form.addRow(t("settings.spell_language", "Idioma principal"), self.spell_lang_box)

        extras = (getattr(state, "spell_extra_languages", "") or "").replace(" ", "")
        self.spell_en_box = QCheckBox("English (US) adicional", g)
        self.spell_en_box.setChecked("en_US" in extras.split(",") if extras else False)
        self.spell_es_box = QCheckBox("Español adicional", g)
        self.spell_es_box.setChecked("es_ES" in extras.split(",") if extras else False)
        self.spell_pt_box = QCheckBox("Português (Brasil) adicional", g)
        self.spell_pt_box.setChecked("pt_BR" in extras.split(",") if extras else False)
        form.addRow(t("settings.spell_extra", "Idiomas extras (união)"), QLabel(""))
        form.addRow(self.spell_pt_box)
        form.addRow(self.spell_en_box)
        form.addRow(self.spell_es_box)

        lay.addWidget(g)
        lay.addWidget(
            self._hint(
                t(
                    "settings.spell_hint",
                    "Por arquivo: clique em Spell na barra de status para "
                    "ativar/desativar idiomas. Idiomas extras formam união "
                    "de dicionários no padrão de novos arquivos.",
                ),
                page,
            )
        )
        lay.addStretch(1)
        return self._wrap_scroll(page)

    def _page_design(self, state: SessionState) -> QWidget:
        t = self._t
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        theme_g = QGroupBox(t("settings.theme_group", "Tema e ícones"), page)
        form = QFormLayout(theme_g)
        form.setSpacing(8)
        form.setContentsMargins(12, 16, 12, 12)

        self.theme_box = QComboBox(theme_g)
        for tid, label in NATIVE_THEMES.items():
            self.theme_box.addItem(t(f"theme.{tid}", label), tid)
        idx = self.theme_box.findData(state.theme or "luminous_void")
        self.theme_box.setCurrentIndex(max(0, idx))
        form.addRow(t("settings.theme", "Tema visual"), self.theme_box)

        self.icon_pack_box = QComboBox(theme_g)
        current_pack = getattr(state, "icon_pack", None) or "qlementine"
        for pack_id, default_label in ICON_PACKS:
            if pack_id == "qlementine":
                label = t("settings.icon_pack_qlementine", "Qlementine (Qt)")
            elif pack_id == "material":
                label = t(
                    "settings.icon_pack_material",
                    "Material Design (outline / light)",
                )
            else:
                label = default_label
            self.icon_pack_box.addItem(label, pack_id)
        pidx = self.icon_pack_box.findData(current_pack)
        self.icon_pack_box.setCurrentIndex(max(0, pidx))
        form.addRow(t("settings.icon_pack", "Pacote de ícones"), self.icon_pack_box)
        lay.addWidget(theme_g)

        vis = QGroupBox(t("settings.transparency", "Transparência"), page)
        vis_form = QVBoxLayout(vis)
        vis_form.setSpacing(6)
        vis_form.setContentsMargins(12, 16, 12, 12)

        self.opacity_slider = QSlider(Qt.Orientation.Horizontal, vis)
        self.opacity_slider.setRange(55, 100)
        self.opacity_slider.setValue(round(state.window_opacity * 100))
        self.opacity_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.opacity_slider.setTickInterval(5)
        self.opacity_label = QLabel(self._opacity_text(), vis)
        self.opacity_slider.valueChanged.connect(self._on_opacity)
        opac_row = QHBoxLayout()
        opac_row.addWidget(QLabel(t("settings.opacity", "Opacidade da janela"), vis))
        opac_row.addWidget(self.opacity_slider, 1)
        opac_row.addWidget(self.opacity_label)
        vis_form.addLayout(opac_row)

        self.chrome_box = QCheckBox(t("settings.chrome", "Chrome translúcido (efeito vidro)"), vis)
        self.chrome_box.setChecked(state.chrome_transparency)
        vis_form.addWidget(self.chrome_box)

        self.editor_box = QCheckBox(t("settings.editor_alpha", "Editor translúcido"), vis)
        self.editor_box.setChecked(state.editor_transparency)
        vis_form.addWidget(self.editor_box)
        lay.addWidget(vis)
        lay.addStretch(1)
        return self._wrap_scroll(page)

    def _page_graphics(self, state: SessionState) -> QWidget:
        t = self._t
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        gfx = QGroupBox(t("settings.graphics", "Aceleração gráfica"), page)
        gfx_form = QVBoxLayout(gfx)
        gfx_form.setSpacing(6)
        gfx_form.setContentsMargins(12, 16, 12, 12)

        self.gpu_box = QCheckBox(t("settings.gpu", "Aceleração por GPU (composição OpenGL)"), gfx)
        self.gpu_box.setChecked(state.gpu_acceleration)
        self.msaa_box = QCheckBox(t("settings.msaa", "Anti-aliasing multisample (MSAA 4x)"), gfx)
        self.msaa_box.setChecked(state.gpu_multisample)
        self.aa_box = QCheckBox(t("settings.aa", "Anti-aliasing de texto e interface"), gfx)
        self.aa_box.setChecked(state.antialiasing)
        self.gpu_box.toggled.connect(self._sync_gpu_deps)
        gfx_form.addWidget(self.gpu_box)
        gfx_form.addWidget(self.msaa_box)
        gfx_form.addWidget(self.aa_box)
        gfx_form.addWidget(
            self._hint(
                t(
                    "settings.gpu_hint",
                    "Alterar GPU ou MSAA exige reiniciar o MagicEditor.",
                ),
                gfx,
            )
        )
        lay.addWidget(gfx)
        lay.addStretch(1)
        return self._wrap_scroll(page)

    def _page_tabs(self, state: SessionState) -> QWidget:
        t = self._t
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        g = QGroupBox(t("settings.tabs_chrome", "Aparência das abas"), page)
        form = QFormLayout(g)
        form.setSpacing(8)
        form.setContentsMargins(12, 16, 12, 12)

        self.tab_height_spin = QSpinBox(g)
        self.tab_height_spin.setRange(22, 40)
        self.tab_height_spin.setSuffix(" px")
        self.tab_height_spin.setValue(int(getattr(state, "tab_height", 28) or 28))
        form.addRow(t("settings.tab_height", "Altura da aba"), self.tab_height_spin)

        self.tab_min_spin = QSpinBox(g)
        self.tab_min_spin.setRange(48, 160)
        self.tab_min_spin.setSuffix(" px")
        self.tab_min_spin.setValue(int(getattr(state, "tab_min_width", 72) or 72))
        form.addRow(t("settings.tab_min_width", "Largura mínima"), self.tab_min_spin)

        self.tab_max_spin = QSpinBox(g)
        self.tab_max_spin.setRange(120, 400)
        self.tab_max_spin.setSuffix(" px")
        self.tab_max_spin.setValue(int(getattr(state, "tab_max_width", 220) or 220))
        form.addRow(t("settings.tab_max_width", "Largura máxima"), self.tab_max_spin)

        lay.addWidget(g)

        beh = QGroupBox(t("settings.tabs_group", "Comportamento"), page)
        bform = QFormLayout(beh)
        bform.setSpacing(8)
        bform.setContentsMargins(12, 16, 12, 12)

        self.tab_scroll_box = QCheckBox(
            t("settings.tab_scroll_buttons", "Botões de navegação ◀ ▶"), beh
        )
        self.tab_scroll_box.setChecked(bool(getattr(state, "show_tab_scroll_buttons", True)))
        bform.addRow(self.tab_scroll_box)

        self.middle_close_box = QCheckBox(
            t("settings.middle_click_close", "Clique do meio fecha a aba"), beh
        )
        self.middle_close_box.setChecked(bool(getattr(state, "middle_click_close", True)))
        bform.addRow(self.middle_close_box)

        self.confirm_close_box = QCheckBox(
            t(
                "settings.confirm_close_unsaved",
                "Perguntar ao fechar aba com alterações",
            ),
            beh,
        )
        self.confirm_close_box.setChecked(bool(getattr(state, "confirm_close_unsaved", True)))
        bform.addRow(self.confirm_close_box)

        info = QLabel(
            t(
                "settings.tabs_info",
                "• Duplo clique na área vazia → novo arquivo\n"
                "• Botão + → novo arquivo\n"
                "• Arraste abas para reordenar\n"
                "• Clique direito → grupos de abas",
            ),
            beh,
        )
        info.setWordWrap(True)
        bform.addRow(info)
        lay.addWidget(beh)
        lay.addStretch(1)
        return self._wrap_scroll(page)

    def _page_performance(self, state: SessionState) -> QWidget:
        t = self._t
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        g = QGroupBox(t("settings.perf_group", "Desempenho e extras"), page)
        form = QFormLayout(g)
        form.setSpacing(8)
        form.setContentsMargins(12, 16, 12, 12)

        self.minimap_box = QCheckBox(t("settings.minimap", "Mostrar minimap"), g)
        self.minimap_box.setChecked(bool(getattr(state, "show_minimap", False)))
        form.addRow(self.minimap_box)

        self.autosave_spin = QSpinBox(g)
        self.autosave_spin.setRange(0, 3600)
        self.autosave_spin.setSuffix(" s")
        self.autosave_spin.setSpecialValueText(t("settings.autosave_off", "Desligado"))
        self.autosave_spin.setValue(int(getattr(state, "autosave_interval_sec", 0) or 0))
        form.addRow(t("settings.autosave", "Autosave"), self.autosave_spin)

        form.addRow(
            self._hint(
                t(
                    "settings.perf_hint",
                    "Arquivos grandes usam mmap + viewport automático. "
                    "Ortografia e realce atuam só na área visível. "
                    "Minimap e autosave podem aumentar o uso de CPU em "
                    "documentos muito grandes.",
                ),
                g,
            )
        )
        lay.addWidget(g)
        lay.addStretch(1)
        return self._wrap_scroll(page)

    def _opacity_text(self) -> str:
        return f"{self.opacity_slider.value()}%"

    def _on_opacity(self, _v: int) -> None:
        self.opacity_label.setText(self._opacity_text())

    def _sync_gpu_deps(self, enabled: bool) -> None:
        self.msaa_box.setEnabled(enabled)

    def apply_to_state(self, state: SessionState) -> SessionState:
        """Mutate and return ``state`` with dialog values."""
        lang = self.lang_box.currentData()
        state.language = str(lang) if lang else state.language
        state.restore_session = self.restore_session_box.isChecked()
        state.show_toolbar = self.show_toolbar_box.isChecked()
        state.show_status_bar = self.show_status_box.isChecked()
        state.recent_files_max = int(self.recent_max_spin.value())
        state.editor_context_menu = self.context_menu_box.isChecked()
        state.show_splash = self.splash_box.isChecked()

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
        state.trim_trailing_on_save = self.trim_save_box.isChecked()
        state.insert_final_newline = self.final_nl_box.isChecked()
        state.high_contrast = self.high_contrast_box.isChecked()

        state.spell_check = self.spell_box.isChecked()
        state.spell_force = True if self.spell_all_box.isChecked() else None
        slang = self.spell_lang_box.currentData()
        state.spell_language = str(slang) if slang else "pt_BR"
        extras: list[str] = []
        primary = state.spell_language
        if self.spell_pt_box.isChecked() and primary != "pt_BR":
            extras.append("pt_BR")
        if self.spell_en_box.isChecked() and primary != "en_US":
            extras.append("en_US")
        if self.spell_es_box.isChecked() and primary != "es_ES":
            extras.append("es_ES")
        state.spell_extra_languages = ",".join(extras)

        theme = self.theme_box.currentData()
        state.theme = str(theme) if theme else state.theme
        pack = self.icon_pack_box.currentData()
        state.icon_pack = str(pack) if pack else "qlementine"
        state.window_opacity = self.opacity_slider.value() / 100.0
        state.chrome_transparency = self.chrome_box.isChecked()
        state.editor_transparency = self.editor_box.isChecked()

        state.gpu_acceleration = self.gpu_box.isChecked()
        state.gpu_multisample = self.msaa_box.isChecked()
        state.antialiasing = self.aa_box.isChecked()

        state.tab_height = int(self.tab_height_spin.value())
        state.tab_min_width = int(self.tab_min_spin.value())
        state.tab_max_width = max(int(self.tab_max_spin.value()), state.tab_min_width)
        state.show_tab_scroll_buttons = self.tab_scroll_box.isChecked()
        state.middle_click_close = self.middle_close_box.isChecked()
        state.confirm_close_unsaved = self.confirm_close_box.isChecked()

        state.show_minimap = self.minimap_box.isChecked()
        state.autosave_interval_sec = int(self.autosave_spin.value())
        return state
