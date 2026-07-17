"""Settings dialog — vertical subject tabs with many customizable options."""

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
    """Multi-pane settings: Geral · Editor · Design · Gráficos · Abas · Avançado."""

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
        self.setMinimumSize(640, 480)
        self.resize(720, 540)
        self.setObjectName("settingsDialog")

        def t(key: str, default: str) -> str:
            if self._tr is not None:
                return self._tr.t(key, default)
            return default

        self._t = t
        self.setWindowTitle(t("settings.title", "Configurações"))

        # --- Left nav (vertical subjects) ---
        self.nav = QListWidget(self)
        self.nav.setObjectName("settingsNav")
        self.nav.setFixedWidth(168)
        self.nav.setSpacing(2)
        subjects = [
            ("general", t("settings.tab.general", "Geral")),
            ("editor", t("settings.tab.editor", "Editor")),
            ("design", t("settings.tab.design", "Design")),
            ("graphics", t("settings.tab.graphics", "Gráficos")),
            ("tabs", t("settings.tab.tabs", "Abas")),
            ("advanced", t("settings.tab.advanced", "Avançado")),
        ]
        for _sid, label in subjects:
            item = QListWidgetItem(label)
            self.nav.addItem(item)

        self.stack = QStackedWidget(self)
        self.stack.addWidget(self._page_general(state))
        self.stack.addWidget(self._page_editor(state))
        self.stack.addWidget(self._page_design(state))
        self.stack.addWidget(self._page_graphics(state))
        self.stack.addWidget(self._page_tabs(state))
        self.stack.addWidget(self._page_advanced(state))

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

        # Language list
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

    # --- pages --------------------------------------------------------

    def _wrap_scroll(self, inner: QWidget) -> QWidget:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(inner)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        return scroll

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
        form.addRow(t("settings.language", "Idioma da interface"), self.lang_box)

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

        lay.addWidget(g)
        tip = QLabel(
            t(
                "settings.general_hint",
                "Idioma e restauração de sessão aplicam-se ao confirmar. "
                "Atalhos de menu usam o idioma da interface.",
            ),
            page,
        )
        tip.setWordWrap(True)
        tip.setObjectName("findDialogStatus")
        lay.addWidget(tip)
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

        self.word_wrap_box = QCheckBox(t("settings.word_wrap", "Quebra de linha"), g)
        self.word_wrap_box.setChecked(state.word_wrap)
        form.addRow(self.word_wrap_box)

        self.line_numbers_box = QCheckBox(
            t("settings.line_numbers", "Números de linha"), g
        )
        self.line_numbers_box.setChecked(state.line_numbers)
        form.addRow(self.line_numbers_box)

        self.highlight_line_box = QCheckBox(
            t("settings.highlight_line", "Destacar linha atual"), g
        )
        self.highlight_line_box.setChecked(state.highlight_current_line)
        form.addRow(self.highlight_line_box)

        lay.addWidget(g)
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

        pack_hint = QLabel(
            t(
                "settings.icon_pack_hint",
                "Qlementine: set moderno para apps Qt. "
                "Material: Material Design Icons (outline), via QtAwesome.",
            ),
            theme_g,
        )
        pack_hint.setWordWrap(True)
        pack_hint.setObjectName("findDialogStatus")
        form.addRow(pack_hint)

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

        self.chrome_box = QCheckBox(
            t("settings.chrome", "Chrome translúcido (efeito vidro)"), vis
        )
        self.chrome_box.setChecked(state.chrome_transparency)
        vis_form.addWidget(self.chrome_box)

        self.editor_box = QCheckBox(t("settings.editor_alpha", "Editor translúcido"), vis)
        self.editor_box.setChecked(state.editor_transparency)
        vis_form.addWidget(self.editor_box)

        tip = QLabel(
            t(
                "settings.opacity_hint",
                "Opacidade e vidro aplicam-se imediatamente. "
                "No Windows, o desfoque acrylic completo é limitado.",
            ),
            vis,
        )
        tip.setWordWrap(True)
        tip.setObjectName("findDialogStatus")
        vis_form.addWidget(tip)

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

        self.gpu_box = QCheckBox(
            t("settings.gpu", "Aceleração por GPU (composição OpenGL)"), gfx
        )
        self.gpu_box.setChecked(state.gpu_acceleration)
        self.msaa_box = QCheckBox(
            t("settings.msaa", "Anti-aliasing multisample (MSAA 4x)"), gfx
        )
        self.msaa_box.setChecked(state.gpu_multisample)
        self.aa_box = QCheckBox(
            t("settings.aa", "Anti-aliasing de texto e interface"), gfx
        )
        self.aa_box.setChecked(state.antialiasing)
        self.gpu_box.toggled.connect(self._sync_gpu_deps)

        gpu_hint = QLabel(
            t(
                "settings.gpu_hint",
                "O modo GPU é configurado antes da inicialização. "
                "Alterar GPU ou MSAA exige reiniciar o MagicEditor.",
            ),
            gfx,
        )
        gpu_hint.setWordWrap(True)
        gpu_hint.setObjectName("findDialogStatus")

        gfx_form.addWidget(self.gpu_box)
        gfx_form.addWidget(self.msaa_box)
        gfx_form.addWidget(self.aa_box)
        gfx_form.addWidget(gpu_hint)

        lay.addWidget(gfx)
        lay.addStretch(1)
        return self._wrap_scroll(page)

    def _page_tabs(self, state: SessionState) -> QWidget:
        t = self._t
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        g = QGroupBox(t("settings.tabs_group", "Comportamento das abas"), page)
        form = QVBoxLayout(g)
        form.setSpacing(8)
        form.setContentsMargins(12, 16, 12, 12)

        info = QLabel(
            t(
                "settings.tabs_info",
                "• Duplo clique na área vazia da barra de abas → novo arquivo\n"
                "• Botão + no canto direito da barra → novo arquivo\n"
                "• Arraste uma aba pelo título para reordenar\n"
                "• Clique do meio em uma aba → fechar",
            ),
            g,
        )
        info.setWordWrap(True)
        form.addWidget(info)

        self.dbl_new_box = QCheckBox(
            t(
                "settings.dblclick_new",
                "Duplo clique na barra cria novo arquivo (sempre ativo)",
            ),
            g,
        )
        self.dbl_new_box.setChecked(True)
        self.dbl_new_box.setEnabled(False)
        form.addWidget(self.dbl_new_box)

        self.movable_tabs_box = QCheckBox(
            t("settings.movable_tabs", "Permitir reordenar abas arrastando (sempre ativo)"),
            g,
        )
        self.movable_tabs_box.setChecked(True)
        self.movable_tabs_box.setEnabled(False)
        form.addWidget(self.movable_tabs_box)

        lay.addWidget(g)
        lay.addStretch(1)
        return self._wrap_scroll(page)

    def _page_advanced(self, state: SessionState) -> QWidget:
        t = self._t
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        g = QGroupBox(t("settings.advanced_group", "Avançado"), page)
        form = QVBoxLayout(g)
        form.setSpacing(8)
        form.setContentsMargins(12, 16, 12, 12)

        note = QLabel(
            t(
                "settings.advanced_hint",
                "Preferências de desempenho e sessão. Arquivos enormes usam "
                "mmap + piece table automaticamente — não carregam o arquivo "
                "inteiro na memória.",
            ),
            g,
        )
        note.setWordWrap(True)
        note.setObjectName("findDialogStatus")
        form.addWidget(note)

        self.restore_session_adv = QLabel(
            t(
                "settings.session_note",
                "Sessão: abas abertas, rascunhos Untitled, marcadores e "
                "posição do cursor são salvos ao fechar.",
            ),
            g,
        )
        self.restore_session_adv.setWordWrap(True)
        form.addWidget(self.restore_session_adv)

        lay.addWidget(g)
        lay.addStretch(1)
        return self._wrap_scroll(page)

    # --- helpers ------------------------------------------------------

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

        state.font_size = int(self.font_size_spin.value())
        state.tab_width = int(self.tab_width_spin.value())
        state.indent_with_spaces = self.indent_spaces_box.isChecked()
        state.word_wrap = self.word_wrap_box.isChecked()
        state.line_numbers = self.line_numbers_box.isChecked()
        state.highlight_current_line = self.highlight_line_box.isChecked()

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
        return state
