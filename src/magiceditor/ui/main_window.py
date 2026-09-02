"""Primary application window — modern daily-driver editor chrome."""

from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QAction, QActionGroup, QCloseEvent, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QDockWidget,
    QFileDialog,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QWidget,
)

from magiceditor.core.encoding import ENCODING_CATALOG
from magiceditor.core.spell import SUPPORTED_SPELL_LANGS
from magiceditor.core.syntax.detect import language_label
from magiceditor.i18n.translator import TranslatorManager
from magiceditor.services.document import Document
from magiceditor.services.document_io import open_document
from magiceditor.services.graphics import (
    apply_translucent_chrome,
    apply_window_opacity,
    graphics_status_summary,
)
from magiceditor.services.settings import AppSettings, SessionState, normalize_path
from magiceditor.themes.manager import ThemeManager
from magiceditor.ui.about_dialog import AboutDialog
from magiceditor.ui.confirm_dialog import ConfirmDialog, ConfirmResult
from magiceditor.ui.document_tools import READ_ONLY_SUFFIX, DocumentToolsMixin
from magiceditor.ui.editor_tab import EditorTab
from magiceditor.ui.find_dialog import FindDialog
from magiceditor.ui.find_in_files_dialog import FindInFilesDialog
from magiceditor.ui.first_run_dialog import FirstRunDialog
from magiceditor.ui.goto_line_dialog import GoToLineDialog
from magiceditor.ui.icons import (
    get_icon_pack,
    language_icon,
    set_icon_pack,
    toolbar_icon_color,
)
from magiceditor.ui.outline_dialog import OutlineDialog
from magiceditor.ui.power_features import PowerFeaturesMixin
from magiceditor.ui.quick_open import QuickOpenDialog
from magiceditor.ui.settings_dialog import SettingsDialog
from magiceditor.ui.sidebar import Sidebar
from magiceditor.ui.status_bar import EditorStatusBar
from magiceditor.ui.tab_manager import TabManager
from magiceditor.ui.virtual_editor import VirtualEditor

_log = logging.getLogger(__name__)


class MainWindow(DocumentToolsMixin, PowerFeaturesMixin, QMainWindow):
    def __init__(
        self,
        translator: TranslatorManager | None = None,
        themes: ThemeManager | None = None,
        settings: AppSettings | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._tr = translator or TranslatorManager()
        self._themes = themes or ThemeManager()
        self._settings = settings or AppSettings()
        self._session = self._settings.load()
        self._untitled_seq = 1
        self._word_wrap = self._session.word_wrap
        # Default ON via AppSettings when key is absent; session can still turn off.
        self._line_numbers = self._session.line_numbers
        self._workspace: Path | None = (
            Path(self._session.workspace) if self._session.workspace else None
        )
        self._restoring = False
        self._icon_color = toolbar_icon_color(self._session.theme)
        set_icon_pack(getattr(self._session, "icon_pack", None) or "qlementine")

        self.setWindowTitle("MagicEditor")
        self.setMinimumSize(900, 560)
        self.resize(1280, 820)
        try:
            from magiceditor.ui.app_icon import load_app_icon

            _app_icon = load_app_icon()
            if not _app_icon.isNull():
                self.setWindowIcon(_app_icon)
        except Exception:
            pass

        self.tabs = TabManager(self)
        self.tabs.set_translator(self._tr)
        self.tabs.set_close_icon_color(self._icon_color)
        self.setCentralWidget(self.tabs)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.tabs.empty_area_double_clicked.connect(self.new_document)
        self._recent_menu = None  # type: ignore[assignment]
        self._menu_format = None  # type: ignore[assignment]
        self._menu_encoding = None  # type: ignore[assignment]
        self._menu_eol = None  # type: ignore[assignment]
        self._menu_convert = None  # type: ignore[assignment]
        self._menu_insert = None  # type: ignore[assignment]

        self._status = EditorStatusBar(self)
        self._status.set_translator(self._tr)
        self.setStatusBar(self._status)
        self._status.spell_clicked.connect(self._show_spell_language_menu)

        self._sidebar = Sidebar(self)
        self._sidebar_dock = QDockWidget("Explorer", self)
        self._sidebar_dock.setObjectName("sidebarDock")
        self._sidebar_dock.setTitleBarWidget(None)  # keep native title; style via QSS
        self._sidebar_dock.setWidget(self._sidebar)
        self._sidebar_dock.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._sidebar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._sidebar.setAutoFillBackground(True)
        self._sidebar_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._sidebar_dock)
        # Explorer is optional — hidden until a folder/workspace is opened.
        self._sidebar_dock.hide()
        self._sidebar.file_activated.connect(self._on_sidebar_file)
        self._sidebar.search_requested.connect(self.show_find_in_files)
        self._sidebar.settings_requested.connect(self.show_settings)
        self._quick_search: QLineEdit | None = None

        self._actions: dict[str, QAction] = {}
        self._theme_actions: dict[str, QAction] = {}
        self._lang_actions: dict[str, QAction] = {}
        self._syntax_actions: dict[str, QAction] = {}
        self._theme_group = QActionGroup(self)
        self._theme_group.setExclusive(True)
        self._lang_group = QActionGroup(self)
        self._lang_group.setExclusive(True)
        self._syntax_group = QActionGroup(self)
        self._syntax_group.setExclusive(True)

        self._build_actions()
        self._build_menus()
        self._build_toolbar()
        self._apply_icons()

        # Watcher/spell/timers must exist before session restore calls watch_path.
        self._init_power_features()
        self._init_document_tools()

        self._tr.language_changed.connect(self.retranslate_ui)

        # Preferences from last session
        try:
            self._tr.load(self._session.language)
        except OSError:
            try:
                self._tr.load("en_US")
            except OSError:
                pass

        qapp = QApplication.instance()
        if qapp is not None:
            try:
                self._themes.apply(qapp, self._session.theme)
            except (OSError, FileNotFoundError):
                pass

        if self._session.geometry:
            self.restoreGeometry(self._session.geometry)
        if self._session.window_state:
            self.restoreState(self._session.window_state)

        self._restoring = True
        restored = False
        if self._session.restore_session:
            restored = self._restore_session_files()
        self._restoring = False
        if not restored:
            self.new_document()

        if self._workspace and self._workspace.is_dir():
            self._show_workspace(self._workspace, persist=False)

        self._sync_checkables()
        self._apply_chrome_visibility()
        self.retranslate_ui()
        self._sync_spell_to_editors()
        self.apply_minimap_to_tabs()
        self._apply_editor_prefs_to_tabs()
        self._update_status_extras()

    def maybe_show_first_run(self) -> None:
        """Show first-run wizard once (called from app bootstrap)."""
        if getattr(self._session, "first_run_done", False):
            return
        dlg = FirstRunDialog(
            language=self._session.language,
            theme=self._session.theme,
            tr=self._tr,
            languages=self._tr.available_languages() or ["pt_BR", "en_US", "es_ES"],
            parent=self,
        )
        if dlg.exec():
            self._set_language(dlg.selected_language(), persist=True)
            self.apply_theme(dlg.selected_theme(), persist=True)
            self._session.want_file_associations = bool(dlg.want_associations())
        self._session.first_run_done = True
        self._settings.save(self._session)

    def _apply_chrome_visibility(self) -> None:
        """Show/hide toolbar and status bar from session prefs."""
        tb = getattr(self, "_toolbar", None)
        if tb is not None:
            tb.setVisible(bool(self._session.show_toolbar))
        self.statusBar().setVisible(bool(self._session.show_status_bar))

    def _apply_editor_prefs_to_tabs(self) -> None:
        """Push font size, wrap, gutters, indent prefs to open editors."""
        s = self._session
        self._word_wrap = s.word_wrap
        self._line_numbers = s.line_numbers
        self._actions["action.word_wrap"].setChecked(self._word_wrap)
        self._actions["action.line_numbers"].setChecked(self._line_numbers)
        if hasattr(self.tabs, "apply_chrome_prefs"):
            self.tabs.apply_chrome_prefs(
                height=int(getattr(s, "tab_height", 30) or 30),
                min_width=int(getattr(s, "tab_min_width", 72) or 72),
                max_width=int(getattr(s, "tab_max_width", 220) or 220),
                show_scroll_buttons=bool(getattr(s, "show_tab_scroll_buttons", True)),
                middle_click_close=bool(getattr(s, "middle_click_close", True)),
            )
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if not isinstance(w, EditorTab):
                continue
            w.set_word_wrap(s.word_wrap)
            w.set_line_numbers(s.line_numbers)
            if isinstance(w.editor, VirtualEditor):
                w.editor.set_font_point_size(s.font_size)
                w.editor.set_tab_width(s.tab_width)
                w.editor.set_indent_with_spaces(s.indent_with_spaces)
                w.editor.set_highlight_current_line(s.highlight_current_line)
                w.editor.set_show_whitespace(bool(getattr(s, "show_whitespace", False)))
                w.editor.set_brace_match_enabled(bool(getattr(s, "brace_match", True)))
                w.editor.set_syntax_enabled(bool(getattr(s, "syntax_highlight", True)))
                w.editor.set_caret_width(int(getattr(s, "caret_width", 1) or 1))
                w.set_word_completion(bool(getattr(s, "word_completion", False)))
                self._wire_editor_context_menu(w.editor)
            w.set_minimap_visible(bool(getattr(s, "show_minimap", False)))

    # --- chrome -------------------------------------------------------

    def _build_actions(self) -> None:
        from magiceditor.ui.window_chrome import populate_actions

        populate_actions(self)

    def _build_menus(self) -> None:
        from magiceditor.ui.window_chrome import populate_menus

        populate_menus(self)

    def _build_toolbar(self) -> None:
        from magiceditor.ui.window_chrome import populate_toolbar

        populate_toolbar(self)

    def eventFilter(self, obj, event):
        if obj is self._quick_search and event.type() == QEvent.Type.MouseButtonPress:
            self.show_quick_open()
            return True
        return super().eventFilter(obj, event)

    def _apply_icons(self) -> None:
        from magiceditor.ui.window_chrome import populate_icons

        populate_icons(self)

    def _sync_checkables(self) -> None:
        theme = self._themes.current
        for tid, action in self._theme_actions.items():
            action.setChecked(tid == theme)
        lang = self._tr.language
        for code, action in self._lang_actions.items():
            action.setChecked(code == lang)
        self._actions["action.toggle_sidebar"].setChecked(self._sidebar_dock.isVisible())
        self._actions["action.word_wrap"].setChecked(self._word_wrap)
        self._actions["action.line_numbers"].setChecked(self._line_numbers)
        self._actions["action.fullscreen"].setChecked(self.isFullScreen())
        self._sync_syntax_check()

    def _sync_syntax_check(self) -> None:
        tab = self.current_tab()
        current = tab.language if tab is not None else "text"
        for lid, action in self._syntax_actions.items():
            action.setChecked(lid == current)

    def retranslate_ui(self, *_args: object) -> None:
        t = self._tr.t
        self._menu_file.setTitle(t("menu.file", "&Arquivo"))
        self._menu_edit.setTitle(t("menu.edit", "&Editar"))
        self._menu_view.setTitle(t("menu.view", "E&xibir"))
        if getattr(self, "_menu_tools", None) is not None:
            self._menu_tools.setTitle(t("menu.tools", "&Ferramentas"))
        if self._menu_format is not None:
            self._menu_format.setTitle(t("menu.format", "&Formatar"))
        self._menu_syntax.setTitle(t("menu.syntax", "&Sintaxe"))
        self._menu_themes.setTitle(t("menu.themes", "&Temas"))
        self._menu_lang.setTitle(t("menu.ui_language", "&Idioma"))
        self._menu_help.setTitle(t("menu.help", "A&juda"))
        if self._recent_menu is not None:
            self._recent_menu.setTitle(t("menu.recent", "Arquivos recentes"))
        if self._menu_encoding is not None:
            self._menu_encoding.setTitle(t("menu.encoding", "Codificação"))
        if self._menu_eol is not None:
            self._menu_eol.setTitle(t("menu.eol", "Fim de linha"))
        if getattr(self, "_menu_convert", None) is not None:
            self._menu_convert.setTitle(t("menu.convert", "Converter"))
        if getattr(self, "_menu_insert", None) is not None:
            self._menu_insert.setTitle(t("menu.insert", "Inserir"))
        self._sidebar_dock.setWindowTitle(t("panel.explorer", "Explorador"))
        labels = {
            "action.new": t("action.new", "&Novo"),
            "action.open": t("action.open", "&Abrir"),
            "action.open_folder": t("action.open_folder", "Abrir &pasta…"),
            "action.save": t("action.save", "&Salvar"),
            "action.save_as": t("action.save_as", "Salvar &como…"),
            "action.save_all": t("action.save_all", "Salvar &tudo"),
            "action.print": t("action.print", "&Imprimir…"),
            "action.export_pdf": t("action.export_pdf", "&Exportar PDF…"),
            "action.undo": t("action.undo", "&Desfazer"),
            "action.redo": t("action.redo", "&Refazer"),
            "action.cut": t("action.cut", "Recor&tar"),
            "action.copy": t("action.copy", "&Copiar"),
            "action.paste": t("action.paste", "C&olar"),
            "action.select_all": t("action.select_all", "Selecionar t&udo"),
            "action.indent": t("action.indent", "Avançar &indentação"),
            "action.unindent": t("action.unindent", "Recuar indenta&ção"),
            "action.duplicate_line": t("action.duplicate_line", "Duplicar &linha"),
            "action.move_line_up": t("action.move_line_up", "Mover linha para &cima"),
            "action.move_line_down": t("action.move_line_down", "Mover linha para &baixo"),
            "action.sort_lines": t("action.sort_lines", "Ordenar linhas"),
            "action.sort_by_length": t("action.sort_by_length", "Ordenar por comprimento"),
            "action.reverse_lines": t("action.reverse_lines", "Inverter ordem das linhas"),
            "action.remove_duplicate_lines": t(
                "action.remove_duplicate_lines", "Remover linhas duplicadas"
            ),
            "action.remove_consecutive_duplicates": t(
                "action.remove_consecutive_duplicates", "Remover duplicadas consecutivas"
            ),
            "action.join_lines": t("action.join_lines", "Unir linhas"),
            "action.delete_blank_lines": t("action.delete_blank_lines", "Remover linhas em branco"),
            "action.trim_trailing": t("action.trim_trailing", "Remover espaços finais"),
            "action.tabs_to_spaces": t("action.tabs_to_spaces", "Tabs → espaços"),
            "action.spaces_to_tabs": t("action.spaces_to_tabs", "Espaços → tabs"),
            "action.toggle_comment": t("action.toggle_comment", "Comentar / descomentar"),
            "action.add_cursor_next": t("action.add_cursor_next", "Adicionar próximo cursor"),
            "action.select_all_occurrences": t(
                "action.select_all_occurrences", "Selecionar todas as ocorrências"
            ),
            "action.clear_cursors": t("action.clear_cursors", "Limpar multi-cursores"),
            "action.matching_brace": t("action.matching_brace", "Ir ao colchete correspondente"),
            "action.case_upper": t("action.case_upper", "MAIÚSCULAS"),
            "action.case_lower": t("action.case_lower", "minúsculas"),
            "action.case_title": t("action.case_title", "Tipo Título"),
            "action.case_sentence": t("action.case_sentence", "Tipo sentença"),
            "action.case_invert": t("action.case_invert", "Inverter caixa"),
            "action.base64_encode": t("action.base64_encode", "Codificar Base64"),
            "action.base64_decode": t("action.base64_decode", "Decodificar Base64"),
            "action.url_encode": t("action.url_encode", "Codificar URL"),
            "action.url_decode": t("action.url_decode", "Decodificar URL"),
            "action.insert_datetime_iso": t("action.insert_datetime_iso", "Data/hora ISO"),
            "action.insert_date_short": t("action.insert_date_short", "Data (local)"),
            "action.insert_datetime_local": t(
                "action.insert_datetime_local", "Data e hora (local)"
            ),
            "action.insert_timestamp": t("action.insert_timestamp", "Timestamp Unix"),
            "action.toggle_read_only": t("action.toggle_read_only", "Somente leitura"),
            "action.find": t("action.find", "&Localizar"),
            "action.replace": t("action.replace", "&Substituir"),
            "action.find_in_files": t("action.find_in_files", "Localizar nos a&rquivos"),
            "action.goto_line": t("action.goto_line", "&Ir para linha…"),
            "action.goto_anything": t("action.goto_anything", "Ir para qualquer coisa…"),
            "action.command_palette": t("action.command_palette", "Paleta de comandos"),
            "action.toggle_bookmark": t("action.toggle_bookmark", "Alternar &marcador"),
            "action.next_bookmark": t("action.next_bookmark", "Próximo marcador"),
            "action.prev_bookmark": t("action.prev_bookmark", "Marcador anterior"),
            "action.preview": t("action.preview", "Pré-&visualizar"),
            "action.symbols": t("action.symbols", "Lista de símbolos"),
            "action.reload": t("action.reload", "Recarregar do disco"),
            "action.reveal_explorer": t("action.reveal_explorer", "Mostrar no Explorer"),
            "action.copy_path": t("action.copy_path", "Copiar caminho"),
            "action.copy_dir": t("action.copy_dir", "Copiar pasta"),
            "action.compare": t("action.compare", "Comparar arquivos…"),
            "action.split_view": t("action.split_view", "Dividir visualização"),
            "action.toggle_spell": t("action.toggle_spell", "Correção ortográfica"),
            "action.spell_ignore": t("action.spell_ignore", "Ignorar palavra"),
            "action.spell_add": t("action.spell_add", "Adicionar ao dicionário"),
            "action.minimap": t("action.minimap", "Minimap"),
            "action.performance": t("action.performance", "Painel de desempenho"),
            "action.live_browser": t("action.live_browser", "Abrir no navegador"),
            "action.cancel_search": t("action.cancel_search", "Cancelar busca"),
            "action.export_theme": t("action.export_theme", "Exportar tema…"),
            "action.import_theme": t("action.import_theme", "Importar tema…"),
            "action.file_checksum": t("action.file_checksum", "Checksum do arquivo…"),
            "action.doc_stats": t("action.doc_stats", "Estatísticas do documento…"),
            "action.toggle_sidebar": t("action.toggle_sidebar", "Alternar e&xplorador"),
            "action.word_wrap": t("action.word_wrap", "&Quebra de linha"),
            "action.line_numbers": t("action.line_numbers", "&Números de linha"),
            "action.zoom_in": t("action.zoom_in", "Aumentar &zoom"),
            "action.zoom_out": t("action.zoom_out", "Diminuir z&oom"),
            "action.zoom_reset": t("action.zoom_reset", "Zoom &padrão"),
            "action.fullscreen": t("action.fullscreen", "&Tela cheia"),
            "action.always_on_top": t("action.always_on_top", "Sempre no &topo"),
            "action.settings": t("action.settings", "Confi&gurações…"),
            "action.quick_open": t("action.quick_open", "Abrir rapi&damente"),
            "action.outline": t("action.outline", "Estru&tura do documento"),
            "action.close_tab": t("action.close_tab", "Fechar &aba"),
            "action.close_others": t("action.close_others", "Fechar &outras"),
            "action.close_all": t("action.close_all", "Fechar t&odas"),
            "action.exit": t("action.exit", "&Sair"),
            "action.about": t("action.about", "&Sobre"),
        }
        for key, label in labels.items():
            if key in self._actions:
                self._actions[key].setText(label)
                # Tooltip without mnemonic ampersand (&& → literal &)
                tip = label.replace("&&", "\0").replace("&", "").replace("\0", "&")
                sc = self._actions[key].shortcut().toString(QKeySequence.SequenceFormat.NativeText)
                self._actions[key].setToolTip(f"{tip} ({sc})" if sc else tip)
        # Theme menu labels
        for tid, action in self._theme_actions.items():
            action.setText(t(f"theme.{tid}", action.text()))
        if self._quick_search is not None:
            self._quick_search.setPlaceholderText(
                t("toolbar.search_placeholder", "Pesquisar arquivos (Ctrl+E)")
            )
        self._sidebar.retranslate(self._tr)
        self.tabs.retranslate_ui()
        self._status.retranslate_ui()
        self._update_status_extras()
        tab = self.current_tab()
        if tab is not None:
            self._update_status_for(tab)
        else:
            self.setWindowTitle(t("app.name", "MagicEditor"))

    # --- session ------------------------------------------------------

    def _restore_session_files(self) -> bool:
        from magiceditor.ui.window_session import plan_session_restore

        files, drafts = plan_session_restore(self._session)
        opened = False
        active_index = 0
        for op in files:
            try:
                doc = open_document(op.path)
            except OSError as exc:
                _log.warning("Could not restore %s: %s", op.path, exc)
                continue
            tab = self._add_document(doc, activate=False)
            if op.bookmarks:
                tab.set_bookmarks(op.bookmarks)
            if op.cursor:
                tab.goto_line(op.cursor[0], op.cursor[1])
            if op.activate:
                active_index = self.tabs.indexOf(tab)
            opened = True
        for op in drafts:
            doc = Document.from_text(op.text)
            doc.title = op.title
            if op.modified:
                doc.modified = True
            tab = self._add_document(doc, activate=False)
            if op.bookmarks:
                tab.set_bookmarks(op.bookmarks)
            if op.cursor:
                tab.goto_line(op.cursor[0], op.cursor[1])
            if op.activate:
                active_index = self.tabs.indexOf(tab)
            opened = True
        if opened:
            self.tabs.setCurrentIndex(max(0, active_index))
            w = self.current_tab()
            if w is not None:
                self._update_status_for(w)
        return opened

    def _collect_session(self) -> SessionState:
        from magiceditor.ui.window_session import TabSessionView, collect_tabs_into_session

        current = self.current_tab()
        views: list[TabSessionView] = []
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if not isinstance(w, EditorTab):
                continue
            path = w.document.path
            # Draft text is persisted; file-backed tabs restore from disk, so
            # never materialize their text here (up to 2MB decode per tab).
            text = ""
            if path is None:
                try:
                    text = w.document.text()
                except Exception:
                    text = ""
            views.append(
                TabSessionView(
                    path=path,
                    path_is_file=bool(path is not None and path.is_file()),
                    title=w.document.title,
                    text=text,
                    modified=w.document.modified,
                    bookmarks=w.get_bookmarks(),
                    cursor=w.cursor_line_col_1based(),
                    is_current=w is current,
                )
            )
        workspace = None
        if self._workspace is not None and self._workspace.is_dir():
            workspace = normalize_path(self._workspace)
        return collect_tabs_into_session(
            views,
            self._session,
            workspace=workspace,
            theme=self._themes.current,
            language=self._tr.language,
            word_wrap=self._word_wrap,
            line_numbers=self._line_numbers,
            icon_pack=get_icon_pack(),
            geometry=self.saveGeometry(),
            window_state=self.saveState(),
        )

    def apply_graphics_preferences(self) -> None:
        """Apply opacity / glass / editor translucency from session."""
        s = self._session
        apply_window_opacity(self, s.window_opacity)
        apply_translucent_chrome(self, s.chrome_transparency)
        self._apply_editor_transparency(s.editor_transparency)
        self._apply_virtual_palette()
        self._status.showMessage(
            graphics_status_summary(
                gpu=s.gpu_acceleration,
                multisample=s.gpu_multisample,
                opacity=s.window_opacity,
                chrome_transparency=s.chrome_transparency,
            ),
            4000,
        )

    def _apply_editor_transparency(self, enabled: bool) -> None:
        name = "translucentEditor" if enabled else ""
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if not isinstance(w, EditorTab):
                continue
            w.editor.setObjectName(name)
            style = w.editor.style()
            if style is not None:
                style.unpolish(w.editor)
                style.polish(w.editor)
            w.editor.update()

    def _apply_virtual_palette(self) -> None:
        """Theme-aware colors for VirtualEditor canvas."""
        theme = self._themes.current
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, EditorTab) and isinstance(w.editor, VirtualEditor):
                w.editor.apply_theme_palette(theme)

    def _apply_preview_theme(self, theme_id: str) -> None:
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, EditorTab):
                w.apply_preview_theme(theme_id)

    def show_settings(self) -> None:
        langs = self._tr.available_languages() or ["pt_BR", "en_US", "es_ES"]
        dlg = SettingsDialog(self._session, self, tr=self._tr, languages=langs)
        if dlg.exec() != SettingsDialog.DialogCode.Accepted:
            return
        old_gpu = self._session.gpu_acceleration
        old_msaa = self._session.gpu_multisample
        old_pack = get_icon_pack()
        old_theme = self._themes.current
        old_lang = self._tr.language
        dlg.apply_to_state(self._session)

        if self._session.theme != old_theme:
            self.apply_theme(self._session.theme, persist=False)
        if self._session.language != old_lang:
            self._set_language(self._session.language, persist=False)
        if hasattr(self, "_spell_engine"):
            self._spell_engine.set_language(
                getattr(self._session, "spell_language", None) or self._session.language
            )
            self._sync_spell_to_editors()
        if hasattr(self, "_apply_autosave_interval"):
            self._apply_autosave_interval()
        if "action.toggle_spell" in self._actions:
            self._actions["action.toggle_spell"].setChecked(
                bool(getattr(self._session, "spell_check", True))
            )
        if "action.minimap" in self._actions:
            self._actions["action.minimap"].setChecked(
                bool(getattr(self._session, "show_minimap", False))
            )
        self._minimap_enabled = bool(getattr(self._session, "show_minimap", False))
        if hasattr(self, "apply_minimap_to_tabs"):
            self.apply_minimap_to_tabs()

        if self._session.icon_pack != old_pack:
            set_icon_pack(self._session.icon_pack)
            self._apply_icons()
            self.tabs.set_close_icon_color(self._icon_color)
            for i in range(self.tabs.count()):
                w = self.tabs.widget(i)
                if isinstance(w, EditorTab):
                    self.tabs.setTabIcon(i, language_icon(w.language, self._icon_color))

        self._apply_editor_prefs_to_tabs()
        self._apply_chrome_visibility()
        self._persist_session()
        self.apply_graphics_preferences()
        if self._session.gpu_acceleration != old_gpu or self._session.gpu_multisample != old_msaa:
            QMessageBox.information(
                self,
                self._tr.t("app.name", "MagicEditor"),
                self._tr.t(
                    "msg.gpu_restart",
                    "As opções de GPU/MSAA são aplicadas na próxima inicialização.\n"
                    "Reinicie o MagicEditor para ativar o novo modo de renderização.",
                ),
            )

    def show_outline(self) -> None:
        tab = self.current_tab()
        if tab is None:
            return
        try:
            raw = tab.document.buffer.get_text(0, min(len(tab.document.buffer), 2_000_000))
            from magiceditor.core.outline_scan import extract_outline_from_bytes

            entries = extract_outline_from_bytes(raw)
        except Exception:
            entries = []
        dlg = OutlineDialog(entries, self, tr=self._tr)
        dlg.line_chosen.connect(lambda line: tab.goto_line(line, 1))
        dlg.exec()

    def show_quick_open(self) -> None:
        open_paths: list[str] = []
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, EditorTab) and w.document.path is not None:
                open_paths.append(str(w.document.path))
        dlg = QuickOpenDialog(self._workspace, self, open_paths=open_paths, tr=self._tr)
        dlg.path_chosen.connect(self.open_path)
        dlg.exec()

    def _on_sidebar_file(self, path: str) -> None:
        # Open editors may emit path or path string key
        p = Path(path)
        if p.is_file():
            self.open_path(p)
            return
        # Try match open tab by path string
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if (
                isinstance(w, EditorTab)
                and w.document.path is not None
                and normalize_path(w.document.path) == path
            ):
                self.tabs.setCurrentIndex(i)
                return

    def _refresh_open_editors_sidebar(self) -> None:
        items: list[tuple[str, str]] = []
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if not isinstance(w, EditorTab):
                continue
            label = w.document.display_name()
            key = normalize_path(w.document.path) if w.document.path is not None else f"tab:{i}"
            items.append((label, key))
        self._sidebar.set_open_editors(items)

    def _persist_session(self) -> None:
        if self._restoring:
            return
        self._settings.save(self._collect_session())

    # --- themes / language --------------------------------------------

    def apply_theme(self, theme_id: str, *, persist: bool = True) -> None:
        qapp = QApplication.instance()
        if qapp is None:
            return
        try:
            self._themes.apply(qapp, theme_id)
        except (OSError, FileNotFoundError) as exc:
            QMessageBox.warning(self, "MagicEditor", str(exc))
            return
        self._icon_color = toolbar_icon_color(theme_id)
        self._apply_icons()
        self.tabs.set_close_icon_color(self._icon_color)
        light = theme_id == "clean_light"
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, EditorTab):
                w.set_syntax_light_theme(light)
                self.tabs.setTabIcon(i, language_icon(w.language, self._icon_color))
        self._apply_virtual_palette()
        self._apply_preview_theme(theme_id)
        self._sync_checkables()
        self._status.showMessage(f"Theme: {theme_id}", 2500)
        if persist:
            self._persist_session()

    def set_syntax_language(self, lang_id: str) -> None:
        tab = self.current_tab()
        if tab is None:
            return
        tab.set_language(lang_id)
        self._sync_syntax_check()
        self._update_status_for(tab)
        self._status.showMessage(f"Syntax: {language_label(lang_id)}", 2000)

    def _set_language(self, lang: str, *, persist: bool = True) -> None:
        try:
            self._tr.load(lang)
        except OSError as exc:
            QMessageBox.warning(self, "MagicEditor", str(exc))
            return
        self._sync_checkables()
        if persist:
            self._persist_session()

    # --- documents ----------------------------------------------------

    def current_tab(self) -> EditorTab | None:
        w = self.tabs.currentWidget()
        return w if isinstance(w, EditorTab) else None

    def new_document(self) -> EditorTab:
        title = f"Untitled-{self._untitled_seq}"
        self._untitled_seq += 1
        tab = self._add_document(Document.blank(title=title))
        self._persist_session()
        return tab

    def open_file_dialog(self) -> None:
        start = str(self._workspace or Path.home())
        path, _ = QFileDialog.getOpenFileName(
            self,
            self._tr.t("action.open", "Open"),
            start,
            "Text (*.txt *.md *.py *.json *.xml *.html *.css *.js *.sql *.log);;All (*.*)",
        )
        if path:
            self.open_path(path)

    def open_folder_dialog(self) -> None:
        start = str(self._workspace or Path.home())
        path = QFileDialog.getExistingDirectory(
            self,
            self._tr.t("action.open_folder", "Open Folder…"),
            start,
        )
        if path:
            self.open_workspace(path)

    def open_workspace(self, path: str | Path) -> None:
        self._show_workspace(Path(path), persist=True)
        self._status.showMessage(f"Workspace: {Path(path).name}", 3000)

    def _show_workspace(self, path: Path, *, persist: bool) -> None:
        self._workspace = path
        self._sidebar.set_root_path(path)
        self._sidebar.set_workspace_label(path.name)
        self._sidebar_dock.show()
        self._actions["action.toggle_sidebar"].setChecked(True)
        self._status.set_sync_message(
            self._tr.t("status.workspace", "Projeto: {name}").format(name=path.name)
        )
        if persist:
            self._persist_session()

    def open_path(self, path: str | Path) -> EditorTab | None:
        from magiceditor.ui.window_files import resolve_open_target

        kind, target = resolve_open_target(path)
        if kind == "workspace":
            self.open_workspace(target)
            return None
        return self._open_file_path(target)

    def _open_file_path(self, path: Path) -> EditorTab | None:
        from magiceditor.ui.window_files import index_of_open_path

        path = Path(path)
        open_paths: list[Path | None] = []
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, EditorTab):
                open_paths.append(w.document.path)
            else:
                open_paths.append(None)
        existing = index_of_open_path(open_paths, path)
        if existing is not None:
            self.tabs.setCurrentIndex(existing)
            self._push_recent(path)
            return self.tabs.widget(existing)
        try:
            doc = open_document(path)
        except OSError as exc:
            _log.warning("Failed to open %s: %s", path, exc)
            QMessageBox.critical(self, "MagicEditor", str(exc))
            return None
        tab = self._add_document(doc)
        self._push_recent(path)
        self._status.showMessage(f"Opened {path.name}", 3000)
        self._persist_session()
        return tab

    def _add_document(self, doc: Document, *, activate: bool = True) -> EditorTab:
        tab = EditorTab(doc, self)
        tab.set_word_wrap(self._word_wrap)
        tab.set_line_numbers(self._line_numbers)
        tab.set_syntax_light_theme(self._themes.current == "clean_light")
        if isinstance(tab.editor, VirtualEditor):
            tab.editor.apply_theme_palette(self._themes.current)
            tab.editor.set_font_point_size(self._session.font_size)
            tab.editor.set_tab_width(self._session.tab_width)
            tab.editor.set_indent_with_spaces(self._session.indent_with_spaces)
            tab.editor.set_highlight_current_line(self._session.highlight_current_line)
            tab.editor.set_show_whitespace(bool(getattr(self._session, "show_whitespace", False)))
            tab.editor.set_brace_match_enabled(bool(getattr(self._session, "brace_match", True)))
            tab.editor.set_syntax_enabled(bool(getattr(self._session, "syntax_highlight", True)))
            tab.editor.set_caret_width(int(getattr(self._session, "caret_width", 1) or 1))
            tab.set_word_completion(bool(getattr(self._session, "word_completion", False)))
            self._wire_editor_context_menu(tab.editor)
        tab.set_minimap_visible(bool(getattr(self._session, "show_minimap", False)))
        if self._session.editor_transparency:
            tab.editor.setObjectName("translucentEditor")
        tab.modification_changed.connect(self._refresh_tab_titles)
        tab.cursor_info_changed.connect(self._status.set_cursor)
        # Selection-dependent actions (Convert submenu) track caret/selection.
        tab.cursor_info_changed.connect(
            lambda *_args, t=tab: self._sync_doc_tool_actions(t)
        )
        tab.language_changed.connect(lambda _lang: self._on_tab_language_changed(tab))
        idx = self.tabs.addTab(tab, doc.display_name())
        self.tabs.setTabIcon(idx, language_icon(tab.language, self._icon_color))
        self._refresh_open_editors_sidebar()
        if activate:
            self.tabs.setCurrentIndex(idx)
            self._update_status_for(tab)
            self._sync_syntax_check()
        if hasattr(self, "_spell_engine"):
            self._sync_spell_to_editors()
        if doc.path is not None and hasattr(self, "watch_path"):
            self.watch_path(str(doc.path))
        return tab

    def _on_tab_language_changed(self, tab: EditorTab) -> None:
        self._sync_syntax_check()
        idx = self.tabs.indexOf(tab)
        if idx >= 0:
            self.tabs.setTabIcon(idx, language_icon(tab.language, self._icon_color))
        if hasattr(self, "_sync_spell_to_editors"):
            self._sync_spell_to_editors()

    def print_current(self) -> None:
        from magiceditor.ui.window_print import print_current as _print

        _print(self)

    def export_pdf_current(self) -> None:
        from magiceditor.ui.window_print import export_pdf_current as _pdf

        _pdf(self)

    def _prepare_document_for_save(self, tab: EditorTab) -> None:
        """Apply trim / final-newline prefs before writing to disk."""
        from magiceditor.ui.window_files import apply_save_prefs_to_document

        tab.sync_document_from_editor()
        s = self._session
        changed = apply_save_prefs_to_document(
            tab.document,
            trim=bool(s.trim_trailing_on_save),
            final_nl=bool(s.insert_final_newline),
        )
        if changed and isinstance(tab.editor, VirtualEditor):
            tab.editor.viewport().update()

    def save_current(self) -> None:
        tab = self.current_tab()
        if tab is None:
            return
        self._prepare_document_for_save(tab)
        if tab.document.path is None:
            self.save_current_as()
            return
        self._run_save_worker(tab, tab.document.path)

    def save_current_as(self) -> None:
        tab = self.current_tab()
        if tab is None:
            return
        self._prepare_document_for_save(tab)
        path, _ = QFileDialog.getSaveFileName(
            self,
            self._tr.t("action.save_as", "Save As"),
            str(tab.document.path or Path.home() / tab.document.title),
            "All (*.*)",
        )
        if not path:
            return
        self._run_save_worker(tab, path)

    def _run_save_worker(self, tab: EditorTab, path: Path | str) -> None:
        from magiceditor.ui.save_worker import SaveWorker, begin_document_save

        prev = getattr(self, "_save_worker", None)
        if isinstance(prev, SaveWorker) and prev.isRunning():
            prev.wait(200)
        self._save_worker = begin_document_save(
            self,
            tab.document,
            path,
            lambda _p, t=tab: self._finish_save(t),
            self._on_save_failed,
        )

    def _on_save_failed(self, message: str) -> None:
        QMessageBox.critical(self, "MagicEditor", message)

    def _finish_save(self, tab: EditorTab) -> None:
        tab.document.modified = False
        if tab.document.path is not None:
            self._push_recent(tab.document.path)
        tab.refresh_language_from_path()
        self._on_tab_language_changed(tab)
        self._refresh_tab_titles()
        self._update_status_for(tab)
        self._status.showMessage("Saved", 2000)
        self._persist_session()

    def show_find(self) -> None:
        tab = self.current_tab()
        if tab is None:
            return
        dlg = FindDialog(tab.editor, self, replace_mode=False, tr=self._tr)
        dlg.exec()

    def show_replace(self) -> None:
        tab = self.current_tab()
        if tab is None:
            return
        dlg = FindDialog(tab.editor, self, replace_mode=True, tr=self._tr)
        dlg.exec()

    def show_find_in_files(self) -> None:
        self.reset_search_cancel()
        dlg = FindInFilesDialog(
            self._workspace,
            self,
            open_sources=self._collect_open_sources(),
            tr=self._tr,
            is_cancelled=self.is_search_cancelled,
            on_cancel_request=self.cancel_long_search,
            on_search_start=self.reset_search_cancel,
        )
        dlg.hit_activated.connect(self._open_search_hit)
        dlg.exec()

    def _collect_open_sources(self) -> list[tuple[str, str, str]]:
        """Return ``(source_key, label, content)`` for each open tab."""
        sources: list[tuple[str, str, str]] = []
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if not isinstance(w, EditorTab):
                continue
            key = f"tab:{i}"
            label = w.document.display_name()
            if w.document.path is not None:
                label = str(w.document.path)
            sources.append((key, label, w.export_text()))
        return sources

    def show_goto_line(self) -> None:
        tab = self.current_tab()
        if tab is None:
            return
        dlg = GoToLineDialog(tab.line_count(), tab.current_line(), self, tr=self._tr)
        if dlg.exec() == GoToLineDialog.DialogCode.Accepted:
            tab.goto_line(dlg.line_number(), 1)
            self._update_status_for(tab)

    def toggle_bookmark(self) -> None:
        tab = self.current_tab()
        if tab is not None:
            tab.toggle_bookmark()
            self._persist_session()

    def next_bookmark(self) -> None:
        tab = self.current_tab()
        if tab is not None and tab.next_bookmark():
            self._update_status_for(tab)
            self._persist_session()

    def prev_bookmark(self) -> None:
        tab = self.current_tab()
        if tab is not None and tab.prev_bookmark():
            self._update_status_for(tab)
            self._persist_session()

    def undo_current(self) -> None:
        tab = self.current_tab()
        if tab is not None:
            tab.undo()
            self._refresh_tab_titles()
            self._update_status_for(tab)

    def redo_current(self) -> None:
        tab = self.current_tab()
        if tab is not None:
            tab.redo()
            self._refresh_tab_titles()
            self._update_status_for(tab)

    def cut_current(self) -> None:
        tab = self.current_tab()
        if tab is not None:
            tab.cut()
            self._refresh_tab_titles()
            self._update_status_for(tab)

    def copy_current(self) -> None:
        tab = self.current_tab()
        if tab is not None:
            tab.copy()

    def paste_current(self) -> None:
        tab = self.current_tab()
        if tab is not None:
            tab.paste()
            self._refresh_tab_titles()
            self._update_status_for(tab)

    def select_all_current(self) -> None:
        tab = self.current_tab()
        if tab is not None:
            tab.select_all()

    def indent_current(self) -> None:
        tab = self.current_tab()
        if tab is not None:
            tab.indent()
            self._refresh_tab_titles()

    def unindent_current(self) -> None:
        tab = self.current_tab()
        if tab is not None:
            tab.unindent()
            self._refresh_tab_titles()

    def duplicate_line_current(self) -> None:
        tab = self.current_tab()
        if tab is not None:
            tab.duplicate_line()
            self._refresh_tab_titles()

    def close_current_tab(self) -> None:
        idx = self.tabs.currentIndex()
        if idx >= 0:
            self._close_tab(idx)

    def close_other_tabs(self) -> None:
        current = self.tabs.currentIndex()
        if current < 0:
            return
        # Close from the end so indices stay valid
        for i in range(self.tabs.count() - 1, -1, -1):
            if i != current:
                self._close_tab(i)

    def close_all_tabs(self) -> None:
        for i in range(self.tabs.count() - 1, -1, -1):
            self._close_tab(i)

    def set_current_encoding(self, encoding: str) -> None:
        tab = self.current_tab()
        if tab is None:
            return
        # Accept any codec listed in the catalog (or known to Python)
        known = {code for code, _ in ENCODING_CATALOG}
        if encoding not in known:
            try:
                "test".encode(encoding)
            except LookupError:
                return
        tab.document.set_encoding(encoding)
        self._refresh_tab_titles()
        self._update_status_for(tab)
        self._status.showMessage(f"Encoding → {encoding}", 2500)

    def set_current_eol(self, eol: str) -> None:
        tab = self.current_tab()
        if tab is None:
            return
        if eol not in {"LF", "CRLF", "CR"}:
            return
        tab.document.set_eol(eol)  # type: ignore[arg-type]
        self._refresh_tab_titles()
        self._update_status_for(tab)
        self._status.showMessage(f"EOL → {eol}", 2500)

    def _push_recent(self, path: Path | str) -> None:
        key = normalize_path(path)
        recent = [p for p in self._session.recent_files if p != key]
        recent.insert(0, key)
        self._session.recent_files = recent[:15]
        self._rebuild_recent_menu()

    def _rebuild_recent_menu(self) -> None:
        menu = self._recent_menu
        if menu is None:
            return
        menu.clear()
        files = [p for p in self._session.recent_files if Path(p).is_file()]
        if not files:
            empty = menu.addAction(self._tr.t("menu.recent_empty", "(vazio)"))
            empty.setEnabled(False)
            return
        for p in files[:15]:
            act = menu.addAction(Path(p).name)
            act.setToolTip(p)
            act.triggered.connect(lambda checked=False, path=p: self.open_path(path))
        menu.addSeparator()
        clear = menu.addAction(self._tr.t("menu.recent_clear", "Limpar lista"))
        clear.triggered.connect(self._clear_recent)

    def _clear_recent(self) -> None:
        self._session.recent_files = []
        self._rebuild_recent_menu()
        self._persist_session()

    def _open_search_hit(self, path: str, line: int, column: int, source_key: str = "") -> None:
        tab: EditorTab | None = None
        if source_key.startswith("tab:"):
            try:
                idx = int(source_key.split(":", 1)[1])
            except ValueError:
                idx = -1
            if 0 <= idx < self.tabs.count():
                w = self.tabs.widget(idx)
                if isinstance(w, EditorTab):
                    self.tabs.setCurrentIndex(idx)
                    tab = w
        if tab is None and path:
            p = Path(path)
            if p.is_file():
                tab = self.open_path(p)
        if tab is not None:
            tab.goto_line(line, column)
            self._update_status_for(tab)

    def toggle_preview(self) -> None:
        tab = self.current_tab()
        if tab is None:
            return
        if tab.is_huge:
            self._status.showMessage("Preview disabled in huge-file mode", 3000)
            return
        on = tab.toggle_preview()
        self._status.showMessage("Preview on" if on else "Preview off", 2000)

    def toggle_sidebar(self) -> None:
        visible = not self._sidebar_dock.isVisible()
        self._sidebar_dock.setVisible(visible)
        self._actions["action.toggle_sidebar"].setChecked(visible)
        # Opening explorer without workspace still shows home tree
        if visible and self._workspace is None:
            self._sidebar.set_root_path(Path.home())

    def toggle_word_wrap(self) -> None:
        self._word_wrap = not self._word_wrap
        self._actions["action.word_wrap"].setChecked(self._word_wrap)
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, EditorTab):
                w.set_word_wrap(self._word_wrap)
        self._persist_session()

    def toggle_line_numbers(self) -> None:
        self._line_numbers = not self._line_numbers
        self._actions["action.line_numbers"].setChecked(self._line_numbers)
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, EditorTab):
                w.set_line_numbers(self._line_numbers)
        self._persist_session()

    def zoom_in(self) -> None:
        tab = self.current_tab()
        if tab is not None:
            tab.zoom_in()

    def zoom_out(self) -> None:
        tab = self.current_tab()
        if tab is not None:
            tab.zoom_out()

    def zoom_reset(self) -> None:
        tab = self.current_tab()
        if tab is not None:
            tab.zoom_reset()

    def toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
        self._actions["action.fullscreen"].setChecked(self.isFullScreen())

    def _msg_buttons(self, box: QMessageBox) -> None:
        """Localize standard QMessageBox buttons (simple messages only)."""
        t = self._tr.t
        mapping = {
            QMessageBox.StandardButton.Save: t("dialog.save", "Salvar"),
            QMessageBox.StandardButton.Discard: t("dialog.discard", "Descartar"),
            QMessageBox.StandardButton.Cancel: t("dialog.cancel", "Cancelar"),
            QMessageBox.StandardButton.Yes: t("dialog.yes", "Sim"),
            QMessageBox.StandardButton.No: t("dialog.no", "Não"),
            QMessageBox.StandardButton.Ok: t("dialog.ok", "OK"),
            QMessageBox.StandardButton.Close: t("dialog.close", "Fechar"),
        }
        for std, label in mapping.items():
            btn = box.button(std)
            if btn is not None:
                btn.setText(label)

    def _show_spell_language_menu(self) -> None:
        """Pick one or more spell languages for the current document."""
        tab = self.current_tab()
        menu = QMenu(self)
        menu.setTitle(self._tr.t("spell.menu", "Ortografia do arquivo"))
        labels = {
            "pt_BR": "Português (Brasil)",
            "en_US": "English (US)",
            "es_ES": "Español",
        }
        current: list[str] = []
        if tab is not None and hasattr(self, "_spell_langs_for_tab"):
            current = self._spell_langs_for_tab(tab)
        elif tab is None:
            current = [getattr(self._session, "spell_language", "pt_BR") or "pt_BR"]

        act_toggle = menu.addAction(self._tr.t("action.toggle_spell", "Correção ortográfica"))
        act_toggle.setCheckable(True)
        act_toggle.setChecked(bool(getattr(self._session, "spell_check", True)))
        menu.addSeparator()
        lang_actions: list[tuple[object, str]] = []
        for code in SUPPORTED_SPELL_LANGS:
            act = menu.addAction(labels.get(code, code))
            act.setCheckable(True)
            act.setChecked(code in current)
            lang_actions.append((act, code))
        menu.addSeparator()
        act_ignore = menu.addAction(self._tr.t("action.spell_ignore", "Ignorar palavra"))
        act_add = menu.addAction(self._tr.t("action.spell_add", "Adicionar ao dicionário"))

        # Anchor near spell label
        pos = self._status.mapToGlobal(self._status.rect().bottomRight())
        chosen = menu.exec(pos)
        if chosen is None:
            return
        if chosen is act_toggle:
            self.toggle_spell_check()
            self._actions["action.toggle_spell"].setChecked(
                bool(getattr(self._session, "spell_check", True))
            )
            return
        if chosen is act_ignore:
            self.spell_ignore_word()
            return
        if chosen is act_add:
            self.spell_add_word()
            return
        for act, code in lang_actions:
            if chosen is act:
                self.toggle_tab_spell_language(code)
                return

    def _close_tab(self, index: int) -> None:
        widget = self.tabs.widget(index)
        if (
            isinstance(widget, EditorTab)
            and widget.document.modified
            and bool(getattr(self._session, "confirm_close_unsaved", True))
        ):
            reply = ConfirmDialog.ask_save_changes(
                self,
                name=widget.document.title,
                tr=self._tr,
            )
            if reply == ConfirmResult.CANCEL:
                return
            if reply == ConfirmResult.SAVE:
                self.tabs.setCurrentIndex(index)
                self.save_current()
                if widget.document.modified:
                    return
        self.tabs.removeTab(index)
        if widget is not None:
            widget.deleteLater()
        self._refresh_open_editors_sidebar()
        if self.tabs.count() == 0:
            self.new_document()
        else:
            self._persist_session()

    def _refresh_tab_titles(self) -> None:
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, EditorTab):
                name = w.document.display_name()
                if w.editor.is_read_only():
                    name += READ_ONLY_SUFFIX
                self.tabs.setTabText(i, name)
                if w is self.current_tab():
                    self.setWindowTitle(f"{name} — MagicEditor")
        self._refresh_open_editors_sidebar()

    def _on_tab_changed(self, index: int) -> None:
        w = self.tabs.widget(index)
        if isinstance(w, EditorTab):
            self._update_status_for(w)
            self._refresh_open_editors_sidebar()
            if not self._restoring:
                self._persist_session()

    def _update_status_for(self, tab: EditorTab) -> None:
        doc = tab.document
        self._status.set_encoding(doc.encoding)
        self._status.set_eol(doc.eol)
        label = language_label(tab.language).upper()
        if tab.is_huge:
            label = f"{label} · HUGE"
        if getattr(doc, "_mmap", None) is not None:
            label = f"{label} · mmap"
        self._status.set_filetype(label)
        title = doc.display_name()
        if tab.editor.is_read_only():
            title += READ_ONLY_SUFFIX
        self.setWindowTitle(f"{title} — MagicEditor")
        self._sync_syntax_check()
        self._sync_format_menus(tab)
        if hasattr(self, "_update_status_extras"):
            self._update_status_extras()
        if hasattr(self, "_sync_doc_tool_actions"):
            self._sync_doc_tool_actions(tab)
        if doc.path is not None and hasattr(self, "watch_path"):
            self.watch_path(str(doc.path))

    def _sync_format_menus(self, tab: EditorTab) -> None:
        enc = tab.document.encoding
        eol = tab.document.eol
        if hasattr(self, "_enc_group"):
            for a in self._enc_group.actions():
                a.setChecked(a.data() == enc)
        if hasattr(self, "_eol_group"):
            for a in self._eol_group.actions():
                a.setChecked(a.data() == eol)

    def _about(self) -> None:
        dlg = AboutDialog(self, tr=self._tr, theme_id=self._themes.current)
        dlg.exec()

    def closeEvent(self, event: QCloseEvent | None) -> None:
        if event is None:
            return
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, EditorTab) and w.document.modified:
                reply = ConfirmDialog.ask_yes_no(
                    self,
                    text=self._tr.t(
                        "msg.unsaved_quit",
                        "Há documentos não salvos. Sair mesmo assim?",
                    ),
                    informative=self._tr.t(
                        "msg.unsaved_quit_hint",
                        "Alterações não salvas serão perdidas.",
                    ),
                    tr=self._tr,
                )
                if reply == ConfirmResult.NO:
                    event.ignore()
                    return
                break
        self._persist_session()
        event.accept()
