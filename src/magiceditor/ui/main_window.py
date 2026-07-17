"""Primary application window — modern daily-driver editor chrome."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QEvent, QSize, Qt
from PyQt6.QtGui import QAction, QActionGroup, QCloseEvent, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QDockWidget,
    QFileDialog,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QToolBar,
    QWidget,
)

from magiceditor.core.syntax.detect import language_label, supported_languages
from magiceditor.i18n.translator import TranslatorManager
from magiceditor.services.document import Document
from magiceditor.services.document_io import open_document, save_document
from magiceditor.services.graphics import (
    apply_translucent_chrome,
    apply_window_opacity,
    graphics_status_summary,
)
from magiceditor.services.print_engine import export_pdf, print_plain_text
from magiceditor.services.settings import AppSettings, SessionState, normalize_path
from magiceditor.themes.manager import ThemeManager
from magiceditor.ui.editor_tab import EditorTab
from magiceditor.ui.find_dialog import FindDialog
from magiceditor.ui.find_in_files_dialog import FindInFilesDialog
from magiceditor.ui.goto_line_dialog import GoToLineDialog
from magiceditor.core.encoding import ENCODING_CATALOG
from magiceditor.ui.icons import icon, language_icon, toolbar_icon_color
from magiceditor.ui.about_dialog import AboutDialog
from magiceditor.ui.outline_dialog import OutlineDialog, extract_markdown_outline
from magiceditor.ui.quick_open import QuickOpenDialog
from magiceditor.ui.settings_dialog import SettingsDialog
from magiceditor.ui.sidebar import Sidebar
from magiceditor.ui.status_bar import EditorStatusBar
from magiceditor.ui.tab_manager import TabManager
from magiceditor.ui.virtual_editor import VirtualEditor


class MainWindow(QMainWindow):
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

        self.setWindowTitle("MagicEditor")
        self.setMinimumSize(900, 560)
        self.resize(1280, 820)

        self.tabs = TabManager(self)
        self.tabs.set_close_icon_color(self._icon_color)
        self.setCentralWidget(self.tabs)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.tabs.empty_area_double_clicked.connect(self.new_document)
        self._recent_menu = None  # type: ignore[assignment]
        self._menu_format = None  # type: ignore[assignment]
        self._menu_encoding = None  # type: ignore[assignment]
        self._menu_eol = None  # type: ignore[assignment]

        self._status = EditorStatusBar(self)
        self.setStatusBar(self._status)

        self._sidebar = Sidebar(self)
        self._sidebar_dock = QDockWidget("Explorer", self)
        self._sidebar_dock.setObjectName("sidebarDock")
        self._sidebar_dock.setWidget(self._sidebar)
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
        restored = self._restore_session_files()
        self._restoring = False
        if not restored:
            self.new_document()

        if self._workspace and self._workspace.is_dir():
            self._show_workspace(self._workspace, persist=False)

        self._sync_checkables()
        self.retranslate_ui()

    # --- chrome -------------------------------------------------------

    def _build_actions(self) -> None:
        def act(
            key: str,
            slot,
            shortcut: str | None = None,
            *,
            checkable: bool = False,
        ) -> QAction:
            action = QAction(key, self)
            action.triggered.connect(slot)
            if shortcut:
                action.setShortcut(QKeySequence(shortcut))
                # Survive focus in the editor canvas (QWidget shortcuts alone can fail).
                action.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
            action.setCheckable(checkable)
            self.addAction(action)
            self._actions[key] = action
            return action

        act("action.new", self.new_document, "Ctrl+N")
        act("action.open", self.open_file_dialog, "Ctrl+O")
        act("action.open_folder", self.open_folder_dialog, "Ctrl+K")
        act("action.save", self.save_current, "Ctrl+S")
        act("action.save_as", self.save_current_as, "Ctrl+Shift+S")
        act("action.print", self.print_current, "Ctrl+P")
        act("action.export_pdf", self.export_pdf_current, "Ctrl+Shift+E")
        act("action.undo", self.undo_current, "Ctrl+Z")
        act("action.redo", self.redo_current, "Ctrl+Y")
        self._actions["action.redo"].setShortcuts(
            [QKeySequence("Ctrl+Y"), QKeySequence("Ctrl+Shift+Z")]
        )
        act("action.cut", self.cut_current, "Ctrl+X")
        act("action.copy", self.copy_current, "Ctrl+C")
        act("action.paste", self.paste_current, "Ctrl+V")
        act("action.select_all", self.select_all_current, "Ctrl+A")
        act("action.indent", self.indent_current, "Ctrl+]")
        act("action.unindent", self.unindent_current, "Ctrl+[")
        act("action.duplicate_line", self.duplicate_line_current, "Ctrl+Shift+D")
        act("action.find", self.show_find, "Ctrl+F")
        act("action.replace", self.show_replace, "Ctrl+H")
        act("action.find_in_files", self.show_find_in_files, "Ctrl+Shift+F")
        act("action.goto_line", self.show_goto_line, "Ctrl+G")
        act("action.toggle_bookmark", self.toggle_bookmark, "Ctrl+F2")
        act("action.next_bookmark", self.next_bookmark, "F2")
        act("action.prev_bookmark", self.prev_bookmark, "Shift+F2")
        act("action.preview", self.toggle_preview, "Ctrl+Shift+P")
        act("action.toggle_sidebar", self.toggle_sidebar, "Ctrl+B", checkable=True)
        act("action.word_wrap", self.toggle_word_wrap, "Alt+Z", checkable=True)
        act("action.line_numbers", self.toggle_line_numbers, checkable=True)
        act("action.zoom_in", self.zoom_in, "Ctrl+=")
        act("action.zoom_out", self.zoom_out, "Ctrl+-")
        act("action.zoom_reset", self.zoom_reset, "Ctrl+0")
        act("action.fullscreen", self.toggle_fullscreen, "F11", checkable=True)
        act("action.settings", self.show_settings, "Ctrl+,")
        # Ctrl+P = Print (platform default). Quick Open uses Ctrl+E.
        act("action.quick_open", self.show_quick_open, "Ctrl+E")
        act("action.outline", self.show_outline, "Ctrl+Shift+O")
        act("action.close_tab", self.close_current_tab, "Ctrl+W")
        act("action.close_others", self.close_other_tabs)
        act("action.close_all", self.close_all_tabs)
        act("action.exit", self.close, "Ctrl+Q")

        self._actions["action.word_wrap"].setChecked(self._word_wrap)
        self._actions["action.line_numbers"].setChecked(self._line_numbers)
        self._actions["action.toggle_sidebar"].setChecked(False)

    def _build_menus(self) -> None:
        mb = self.menuBar()
        mb.setNativeMenuBar(False)
        # Titles with & mnemonics come from retranslate_ui (Alt+A → Arquivo, etc.).
        self._menu_file = mb.addMenu("&Arquivo")
        self._menu_edit = mb.addMenu("&Editar")
        self._menu_view = mb.addMenu("E&xibir")
        self._menu_format = mb.addMenu("&Formatar")
        self._menu_syntax = mb.addMenu("&Sintaxe")
        self._menu_themes = mb.addMenu("&Temas")
        self._menu_lang = mb.addMenu("&Idioma da interface")
        self._menu_help = mb.addMenu("A&juda")

        for key in (
            "action.new",
            "action.open",
            "action.open_folder",
            "action.save",
            "action.save_as",
            "action.print",
            "action.export_pdf",
        ):
            self._menu_file.addAction(self._actions[key])
        self._menu_file.addSeparator()
        for key in (
            "action.close_tab",
            "action.close_others",
            "action.close_all",
        ):
            self._menu_file.addAction(self._actions[key])
        self._menu_file.addSeparator()
        self._recent_menu = self._menu_file.addMenu(self._tr.t("menu.recent", "Arquivos recentes"))
        self._rebuild_recent_menu()
        self._menu_file.addSeparator()
        self._menu_file.addAction(self._actions["action.exit"])

        for key in ("action.undo", "action.redo"):
            self._menu_edit.addAction(self._actions[key])
        self._menu_edit.addSeparator()
        for key in (
            "action.cut",
            "action.copy",
            "action.paste",
            "action.select_all",
        ):
            self._menu_edit.addAction(self._actions[key])
        self._menu_edit.addSeparator()
        for key in (
            "action.indent",
            "action.unindent",
            "action.duplicate_line",
        ):
            self._menu_edit.addAction(self._actions[key])
        self._menu_edit.addSeparator()
        for key in (
            "action.find",
            "action.replace",
            "action.find_in_files",
            "action.goto_line",
        ):
            self._menu_edit.addAction(self._actions[key])
        self._menu_edit.addSeparator()
        for key in (
            "action.toggle_bookmark",
            "action.next_bookmark",
            "action.prev_bookmark",
        ):
            self._menu_edit.addAction(self._actions[key])

        for key in (
            "action.preview",
            "action.toggle_sidebar",
            "action.quick_open",
            "action.outline",
            "action.word_wrap",
            "action.line_numbers",
            "action.zoom_in",
            "action.zoom_out",
            "action.zoom_reset",
            "action.fullscreen",
            "action.settings",
        ):
            self._menu_view.addAction(self._actions[key])

        # Format: encoding + EOL
        self._menu_encoding = self._menu_format.addMenu(
            self._tr.t("menu.encoding", "Codificação")
        )
        self._enc_group = QActionGroup(self)
        self._enc_group.setExclusive(True)
        for enc, label in ENCODING_CATALOG:
            a = QAction(label, self)
            a.setCheckable(True)
            a.setData(enc)
            a.triggered.connect(lambda checked=False, e=enc: self.set_current_encoding(e))
            self._enc_group.addAction(a)
            self._menu_encoding.addAction(a)
        self._menu_eol = self._menu_format.addMenu(self._tr.t("menu.eol", "Fim de linha"))
        self._eol_group = QActionGroup(self)
        self._eol_group.setExclusive(True)
        for eol, label in (("LF", "Unix (LF)"), ("CRLF", "Windows (CRLF)"), ("CR", "Classic Mac (CR)")):
            a = QAction(label, self)
            a.setCheckable(True)
            a.setData(eol)
            a.triggered.connect(lambda checked=False, e=eol: self.set_current_eol(e))
            self._eol_group.addAction(a)
            self._menu_eol.addAction(a)

        for lang_id, label in supported_languages():
            action = QAction(label, self)
            action.setCheckable(True)
            action.setData(lang_id)
            action.triggered.connect(
                lambda checked=False, lid=lang_id: self.set_syntax_language(lid)
            )
            self._syntax_group.addAction(action)
            self._menu_syntax.addAction(action)
            self._syntax_actions[lang_id] = action

        for theme_id, label in self._themes.list_themes():
            action = QAction(label, self)
            action.setCheckable(True)
            action.setData(theme_id)
            action.triggered.connect(
                lambda checked=False, t=theme_id: self.apply_theme(t, persist=True)
            )
            self._theme_group.addAction(action)
            self._menu_themes.addAction(action)
            self._theme_actions[theme_id] = action

        for lang in self._tr.available_languages() or ["en_US", "pt_BR"]:
            action = QAction(lang, self)
            action.setCheckable(True)
            action.setData(lang)
            action.triggered.connect(
                lambda checked=False, code=lang: self._set_language(code, persist=True)
            )
            self._lang_group.addAction(action)
            self._menu_lang.addAction(action)
            self._lang_actions[lang] = action

        about = QAction("About", self)
        about.setObjectName("action.about")
        about.triggered.connect(self._about)
        self._actions["action.about"] = about
        self._menu_help.addAction(about)

    def _build_toolbar(self) -> None:
        tb = QToolBar("Main", self)
        tb.setObjectName("mainToolbar")
        tb.setMovable(False)
        tb.setIconSize(QSize(22, 22))
        tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.addToolBar(tb)
        # File
        for key in (
            "action.new",
            "action.open",
            "action.open_folder",
            "action.save",
            "action.print",
        ):
            tb.addAction(self._actions[key])
        tb.addSeparator()
        # History
        for key in ("action.undo", "action.redo"):
            tb.addAction(self._actions[key])
        tb.addSeparator()
        # Clipboard
        for key in ("action.cut", "action.copy", "action.paste"):
            tb.addAction(self._actions[key])
        tb.addSeparator()
        # Search / view
        for key in (
            "action.find",
            "action.replace",
            "action.find_in_files",
            "action.goto_line",
            "action.preview",
            "action.toggle_sidebar",
            "action.settings",
        ):
            tb.addAction(self._actions[key])
        tb.addSeparator()
        # Quick Open field (Ctrl+E; Ctrl+P is Print)
        search = QLineEdit(self)
        search.setObjectName("toolbarSearch")
        search.setPlaceholderText("Pesquisar arquivos (Ctrl+E)")
        search.setClearButtonEnabled(True)
        search.setMinimumWidth(200)
        search.setMaximumWidth(320)
        search.setReadOnly(True)
        search.setCursor(Qt.CursorShape.PointingHandCursor)
        search.installEventFilter(self)
        tb.addWidget(search)
        self._quick_search = search
        self._toolbar = tb

    def eventFilter(self, obj, event):
        if obj is self._quick_search and event.type() == QEvent.Type.MouseButtonPress:
            self.show_quick_open()
            return True
        return super().eventFilter(obj, event)

    def _apply_icons(self) -> None:
        c = self._icon_color
        mapping = {
            "action.new": "new",
            "action.open": "open",
            "action.open_folder": "folder",
            "action.save": "save",
            "action.save_as": "save_as",
            "action.print": "print",
            "action.export_pdf": "export_pdf",
            "action.undo": "undo",
            "action.redo": "redo",
            "action.cut": "cut",
            "action.copy": "copy",
            "action.paste": "paste",
            "action.select_all": "select_all",
            "action.find": "find",
            "action.replace": "replace",
            "action.find_in_files": "find_files",
            "action.goto_line": "goto",
            "action.toggle_bookmark": "bookmark",
            "action.next_bookmark": "bookmark",
            "action.prev_bookmark": "bookmark",
            "action.preview": "preview",
            "action.toggle_sidebar": "sidebar",
            "action.word_wrap": "wrap",
            "action.line_numbers": "lines",
            "action.zoom_in": "zoom_in",
            "action.zoom_out": "zoom_out",
            "action.zoom_reset": "zoom_reset",
            "action.fullscreen": "fullscreen",
            "action.settings": "settings",
            "action.quick_open": "quick_open",
            "action.outline": "outline",
            "action.indent": "indent",
            "action.unindent": "unindent",
            "action.duplicate_line": "duplicate_line",
            "action.close_tab": "close_tab",
            "action.exit": "exit",
            "action.about": "about",
        }
        for key, name in mapping.items():
            if key in self._actions:
                self._actions[key].setIcon(icon(name, c))
        # Syntax menu language icons
        for lang_id, action in self._syntax_actions.items():
            action.setIcon(language_icon(lang_id, c))

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

    def retranslate_ui(self) -> None:
        t = self._tr.t
        self._menu_file.setTitle(t("menu.file", "&Arquivo"))
        self._menu_edit.setTitle(t("menu.edit", "&Editar"))
        self._menu_view.setTitle(t("menu.view", "E&xibir"))
        if self._menu_format is not None:
            self._menu_format.setTitle(t("menu.format", "&Formatar"))
        self._menu_syntax.setTitle(t("menu.syntax", "&Sintaxe"))
        self._menu_themes.setTitle(t("menu.themes", "&Temas"))
        self._menu_lang.setTitle(t("menu.ui_language", "&Idioma da interface"))
        self._menu_help.setTitle(t("menu.help", "A&juda"))
        if self._recent_menu is not None:
            self._recent_menu.setTitle(t("menu.recent", "Arquivos recentes"))
        if self._menu_encoding is not None:
            self._menu_encoding.setTitle(t("menu.encoding", "Codificação"))
        if self._menu_eol is not None:
            self._menu_eol.setTitle(t("menu.eol", "Fim de linha"))
        self._sidebar_dock.setWindowTitle(t("panel.explorer", "Explorador"))
        labels = {
            "action.new": t("action.new", "&Novo"),
            "action.open": t("action.open", "&Abrir"),
            "action.open_folder": t("action.open_folder", "Abrir &pasta…"),
            "action.save": t("action.save", "&Salvar"),
            "action.save_as": t("action.save_as", "Salvar &como…"),
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
            "action.find": t("action.find", "&Localizar"),
            "action.replace": t("action.replace", "&Substituir"),
            "action.find_in_files": t("action.find_in_files", "Localizar nos a&rquivos"),
            "action.goto_line": t("action.goto_line", "&Ir para linha…"),
            "action.toggle_bookmark": t("action.toggle_bookmark", "Alternar &marcador"),
            "action.next_bookmark": t("action.next_bookmark", "Próximo marcador"),
            "action.prev_bookmark": t("action.prev_bookmark", "Marcador anterior"),
            "action.preview": t("action.preview", "Pré-&visualizar"),
            "action.toggle_sidebar": t("action.toggle_sidebar", "Alternar e&xplorador"),
            "action.word_wrap": t("action.word_wrap", "&Quebra de linha"),
            "action.line_numbers": t("action.line_numbers", "&Números de linha"),
            "action.zoom_in": t("action.zoom_in", "Aumentar &zoom"),
            "action.zoom_out": t("action.zoom_out", "Diminuir z&oom"),
            "action.zoom_reset": t("action.zoom_reset", "Zoom &padrão"),
            "action.fullscreen": t("action.fullscreen", "&Tela cheia"),
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
                sc = self._actions[key].shortcut().toString(
                    QKeySequence.SequenceFormat.NativeText
                )
                self._actions[key].setToolTip(f"{tip} ({sc})" if sc else tip)
        # Theme menu labels
        for tid, action in self._theme_actions.items():
            action.setText(t(f"theme.{tid}", action.text()))
        if self._quick_search is not None:
            self._quick_search.setPlaceholderText(
                t("toolbar.search_placeholder", "Pesquisar arquivos (Ctrl+E)")
            )
        self._sidebar.retranslate(self._tr)
        if self._workspace is None:
            self._status.set_sync_message(t("status.sync", "Sincronização: MagicCloud"))
        tab = self.current_tab()
        if tab is not None:
            self._update_status_for(tab)
        else:
            self.setWindowTitle(t("app.name", "MagicEditor"))

    # --- session ------------------------------------------------------

    def _restore_session_files(self) -> bool:
        opened = False
        active_index = 0
        active_key = (
            normalize_path(self._session.active_file)
            if self._session.active_file
            else None
        )
        for path_str in self._session.open_files:
            path = Path(path_str)
            if not path.is_file():
                continue
            try:
                doc = open_document(path)
            except OSError:
                continue
            tab = self._add_document(doc, activate=False)
            key = normalize_path(path)
            # Restore bookmarks (0-based lines)
            marks = self._session.bookmarks.get(key) or self._session.bookmarks.get(path_str)
            if marks:
                tab.set_bookmarks(marks)
            # Restore caret
            cursor = self._session.cursors.get(key) or self._session.cursors.get(path_str)
            if cursor:
                line, col = cursor
                tab.goto_line(line, col)
            if active_key and key == active_key:
                active_index = self.tabs.indexOf(tab)
            opened = True

        # Restore Untitled drafts (unsaved buffers)
        draft_active_idx: int | None = None
        for draft in self._session.drafts:
            text = str(draft.get("text") or "")
            title = str(draft.get("title") or "Untitled")
            doc = Document.from_text(text)
            doc.title = title
            if text:
                doc.modified = True
            tab = self._add_document(doc, activate=False)
            marks = draft.get("bookmarks")
            if isinstance(marks, list):
                tab.set_bookmarks(marks)
            cur = draft.get("cursor")
            if isinstance(cur, (list, tuple)) and len(cur) >= 2:
                try:
                    tab.goto_line(int(cur[0]), int(cur[1]))
                except (TypeError, ValueError):
                    pass
            if draft.get("active"):
                draft_active_idx = self.tabs.indexOf(tab)
            opened = True

        if opened:
            if draft_active_idx is not None and draft_active_idx >= 0:
                active_index = draft_active_idx
            self.tabs.setCurrentIndex(max(0, active_index))
            w = self.current_tab()
            if w is not None:
                self._update_status_for(w)
        return opened

    def _collect_session(self) -> SessionState:
        open_files: list[str] = []
        bookmarks: dict[str, list[int]] = {}
        cursors: dict[str, tuple[int, int]] = {}
        drafts: list[dict] = []
        active: str | None = None
        current = self.current_tab()
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if not isinstance(w, EditorTab):
                continue
            if w.document.path is not None and w.document.path.is_file():
                p = normalize_path(w.document.path)
                open_files.append(p)
                marks = w.get_bookmarks()
                if marks:
                    bookmarks[p] = marks
                cursors[p] = w.cursor_line_col_1based()
                if w is current:
                    active = p
            else:
                # Untitled / unsaved buffer recovery
                try:
                    text = w.document.text()
                except Exception:
                    text = ""
                if not text and not w.document.modified:
                    continue
                entry: dict = {
                    "title": w.document.title,
                    "text": text[:400_000],
                    "bookmarks": w.get_bookmarks(),
                    "cursor": list(w.cursor_line_col_1based()),
                }
                if w is current:
                    entry["active"] = True
                drafts.append(entry)

        workspace = None
        if self._workspace is not None and self._workspace.is_dir():
            workspace = normalize_path(self._workspace)
        # Preserve graphics prefs already loaded (updated via Settings dialog).
        gfx = self._session
        recent = list(self._session.recent_files)
        return SessionState(
            theme=self._themes.current,
            language=self._tr.language,
            word_wrap=self._word_wrap,
            line_numbers=self._line_numbers,
            workspace=workspace,
            open_files=open_files,
            active_file=active,
            bookmarks=bookmarks,
            cursors=cursors,
            drafts=drafts,
            recent_files=recent,
            gpu_acceleration=gfx.gpu_acceleration,
            gpu_multisample=gfx.gpu_multisample,
            antialiasing=gfx.antialiasing,
            window_opacity=gfx.window_opacity,
            chrome_transparency=gfx.chrome_transparency,
            editor_transparency=gfx.editor_transparency,
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

    def show_settings(self) -> None:
        dlg = SettingsDialog(self._session, self, tr=self._tr)
        if dlg.exec() != SettingsDialog.DialogCode.Accepted:
            return
        old_gpu = self._session.gpu_acceleration
        old_msaa = self._session.gpu_multisample
        dlg.apply_to_state(self._session)
        self._persist_session()
        self.apply_graphics_preferences()
        if (
            self._session.gpu_acceleration != old_gpu
            or self._session.gpu_multisample != old_msaa
        ):
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
            text = tab.document.text() if tab.is_huge else (
                tab.editor.toPlainText() if hasattr(tab.editor, "toPlainText") else tab.document.text()
            )
        except Exception:
            text = ""
        # Cap huge-file outline scan to first ~2MB of decoded text
        if len(text) > 2_000_000:
            text = text[:2_000_000]
        entries = extract_markdown_outline(text)
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
            key = (
                normalize_path(w.document.path)
                if w.document.path is not None
                else f"tab:{i}"
            )
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
        path = Path(path)
        # Reuse existing tab if already open
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if (
                isinstance(w, EditorTab)
                and w.document.path is not None
                and w.document.path.resolve() == path.resolve()
            ):
                self.tabs.setCurrentIndex(i)
                self._push_recent(path)
                return w
        try:
            doc = open_document(path)
        except OSError as exc:
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
        if self._session.editor_transparency:
            tab.editor.setObjectName("translucentEditor")
        tab.modification_changed.connect(self._refresh_tab_titles)
        tab.cursor_info_changed.connect(self._status.set_cursor)
        tab.language_changed.connect(lambda _lang: self._on_tab_language_changed(tab))
        idx = self.tabs.addTab(tab, doc.display_name())
        self.tabs.setTabIcon(idx, language_icon(tab.language, self._icon_color))
        self._refresh_open_editors_sidebar()
        if activate:
            self.tabs.setCurrentIndex(idx)
            self._update_status_for(tab)
            self._sync_syntax_check()
        return tab

    def _on_tab_language_changed(self, tab: EditorTab) -> None:
        self._sync_syntax_check()
        idx = self.tabs.indexOf(tab)
        if idx >= 0:
            self.tabs.setTabIcon(idx, language_icon(tab.language, self._icon_color))

    def print_current(self) -> None:
        tab = self.current_tab()
        if tab is None:
            return
        tab.sync_document_from_editor()
        ok = print_plain_text(
            tab.export_text(),
            parent=self,
            title=tab.document.title,
        )
        if ok:
            self._status.showMessage("Sent to printer", 2500)

    def export_pdf_current(self) -> None:
        tab = self.current_tab()
        if tab is None:
            return
        tab.sync_document_from_editor()
        default = Path.home() / f"{Path(tab.document.title).stem or 'document'}.pdf"
        path, _ = QFileDialog.getSaveFileName(
            self,
            self._tr.t("action.export_pdf", "Export PDF…"),
            str(default),
            "PDF (*.pdf)",
        )
        if not path:
            return
        try:
            export_pdf(tab.export_text(), path, title=tab.document.title)
        except OSError as exc:
            QMessageBox.critical(self, "MagicEditor", str(exc))
            return
        self._status.showMessage(f"PDF saved: {Path(path).name}", 3500)

    def save_current(self) -> None:
        tab = self.current_tab()
        if tab is None:
            return
        tab.sync_document_from_editor()
        if tab.document.path is None:
            self.save_current_as()
            return
        try:
            save_document(tab.document)
        except OSError as exc:
            QMessageBox.critical(self, "MagicEditor", str(exc))
            return
        if not tab.is_huge:
            tab.editor.document().setModified(False)  # type: ignore[union-attr]
        tab.document.modified = False
        if tab.document.path is not None:
            self._push_recent(tab.document.path)
        self._refresh_tab_titles()
        self._update_status_for(tab)
        self._status.showMessage("Saved", 2000)
        self._persist_session()

    def save_current_as(self) -> None:
        tab = self.current_tab()
        if tab is None:
            return
        tab.sync_document_from_editor()
        path, _ = QFileDialog.getSaveFileName(
            self,
            self._tr.t("action.save_as", "Save As"),
            str(tab.document.path or Path.home() / tab.document.title),
            "All (*.*)",
        )
        if not path:
            return
        try:
            save_document(tab.document, path)
        except OSError as exc:
            QMessageBox.critical(self, "MagicEditor", str(exc))
            return
        if not tab.is_huge:
            tab.editor.document().setModified(False)  # type: ignore[union-attr]
        tab.document.modified = False
        if tab.document.path is not None:
            self._push_recent(tab.document.path)
        self._refresh_tab_titles()
        self._update_status_for(tab)
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
        dlg = FindInFilesDialog(
            self._workspace,
            self,
            open_sources=self._collect_open_sources(),
            tr=self._tr,
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
        # Refresh classic editor text after in-buffer EOL rewrite
        if not tab.is_huge and not isinstance(tab.editor, VirtualEditor):
            from magiceditor.ui.text_editor import TextEditor

            if isinstance(tab.editor, TextEditor):
                pos = tab.editor.textCursor().position()
                tab.editor.blockSignals(True)
                tab.editor.setPlainText(tab.document.text())
                tab.editor.blockSignals(False)
                cur = tab.editor.textCursor()
                cur.setPosition(min(pos, len(tab.document.text())))
                tab.editor.setTextCursor(cur)
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
        """Localize standard QMessageBox buttons."""
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

    def _close_tab(self, index: int) -> None:
        widget = self.tabs.widget(index)
        if isinstance(widget, EditorTab) and widget.document.modified:
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Icon.Question)
            box.setWindowTitle(self._tr.t("app.name", "MagicEditor"))
            box.setText(
                self._tr.t("msg.save_changes", "Salvar alterações em «{name}»?").format(
                    name=widget.document.title
                )
            )
            box.setStandardButtons(
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel
            )
            self._msg_buttons(box)
            reply = box.exec()
            if reply == QMessageBox.StandardButton.Cancel:
                return
            if reply == QMessageBox.StandardButton.Save:
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
                self.tabs.setTabText(i, w.document.display_name())
                if w is self.current_tab():
                    self.setWindowTitle(f"{w.document.display_name()} — MagicEditor")
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
        self._status.set_filetype(label)
        self.setWindowTitle(f"{doc.display_name()} — MagicEditor")
        self._sync_syntax_check()
        self._sync_format_menus(tab)

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
                box = QMessageBox(self)
                box.setIcon(QMessageBox.Icon.Question)
                box.setWindowTitle(self._tr.t("app.name", "MagicEditor"))
                box.setText(
                    self._tr.t(
                        "msg.unsaved_quit",
                        "Há documentos não salvos. Sair mesmo assim?",
                    )
                )
                box.setStandardButtons(
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                self._msg_buttons(box)
                if box.exec() == QMessageBox.StandardButton.No:
                    event.ignore()
                    return
                break
        self._persist_session()
        event.accept()
