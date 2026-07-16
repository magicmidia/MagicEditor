"""Primary application window — modern daily-driver editor chrome."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QAction, QActionGroup, QCloseEvent, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QDockWidget,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QToolBar,
    QWidget,
)

from magiceditor.core.syntax.detect import language_label, supported_languages
from magiceditor.i18n.translator import TranslatorManager
from magiceditor.services.document import Document
from magiceditor.services.document_io import open_document, save_document
from magiceditor.services.print_engine import export_pdf, print_plain_text
from magiceditor.services.settings import AppSettings, SessionState
from magiceditor.themes.manager import ThemeManager
from magiceditor.ui.editor_tab import EditorTab
from magiceditor.ui.find_dialog import FindDialog
from magiceditor.ui.icons import icon, toolbar_icon_color
from magiceditor.ui.sidebar import Sidebar
from magiceditor.ui.status_bar import EditorStatusBar
from magiceditor.ui.tab_manager import TabManager


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
        self.setCentralWidget(self.tabs)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.tabs.currentChanged.connect(self._on_tab_changed)

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
        self._sidebar.file_activated.connect(self.open_path)

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
            action.setCheckable(checkable)
            self._actions[key] = action
            return action

        act("action.new", self.new_document, "Ctrl+N")
        act("action.open", self.open_file_dialog, "Ctrl+O")
        act("action.open_folder", self.open_folder_dialog, "Ctrl+K")
        act("action.save", self.save_current, "Ctrl+S")
        act("action.save_as", self.save_current_as, "Ctrl+Shift+S")
        act("action.print", self.print_current, "Ctrl+P")
        act("action.export_pdf", self.export_pdf_current, "Ctrl+Shift+E")
        act("action.find", self.show_find, "Ctrl+F")
        act("action.replace", self.show_replace, "Ctrl+H")
        act("action.preview", self.toggle_preview, "Ctrl+Shift+P")
        act("action.toggle_sidebar", self.toggle_sidebar, "Ctrl+B", checkable=True)
        act("action.word_wrap", self.toggle_word_wrap, "Alt+Z", checkable=True)
        act("action.line_numbers", self.toggle_line_numbers, checkable=True)
        act("action.zoom_in", self.zoom_in, "Ctrl+=")
        act("action.zoom_out", self.zoom_out, "Ctrl+-")
        act("action.zoom_reset", self.zoom_reset, "Ctrl+0")
        act("action.fullscreen", self.toggle_fullscreen, "F11", checkable=True)
        act("action.exit", self.close, "Ctrl+Q")

        self._actions["action.word_wrap"].setChecked(self._word_wrap)
        self._actions["action.line_numbers"].setChecked(self._line_numbers)
        self._actions["action.toggle_sidebar"].setChecked(False)

    def _build_menus(self) -> None:
        mb = self.menuBar()
        self._menu_file = mb.addMenu("File")
        self._menu_edit = mb.addMenu("Edit")
        self._menu_view = mb.addMenu("View")
        self._menu_syntax = mb.addMenu("Syntax")
        self._menu_themes = mb.addMenu("Themes")
        self._menu_lang = mb.addMenu("UI Language")
        self._menu_help = mb.addMenu("Help")

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
        self._menu_file.addAction(self._actions["action.exit"])

        for key in ("action.find", "action.replace"):
            self._menu_edit.addAction(self._actions[key])

        for key in (
            "action.preview",
            "action.toggle_sidebar",
            "action.word_wrap",
            "action.line_numbers",
            "action.zoom_in",
            "action.zoom_out",
            "action.zoom_reset",
            "action.fullscreen",
        ):
            self._menu_view.addAction(self._actions[key])

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
        tb.setIconSize(QSize(18, 18))
        tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.addToolBar(tb)
        for key in (
            "action.new",
            "action.open",
            "action.open_folder",
            "action.save",
        ):
            tb.addAction(self._actions[key])
        tb.addSeparator()
        for key in (
            "action.find",
            "action.replace",
            "action.preview",
            "action.toggle_sidebar",
        ):
            tb.addAction(self._actions[key])
        self._toolbar = tb

    def _apply_icons(self) -> None:
        c = self._icon_color
        mapping = {
            "action.new": "new",
            "action.open": "open",
            "action.open_folder": "folder",
            "action.save": "save",
            "action.save_as": "save_as",
            "action.print": "save",
            "action.export_pdf": "save_as",
            "action.find": "find",
            "action.replace": "replace",
            "action.preview": "preview",
            "action.toggle_sidebar": "sidebar",
            "action.word_wrap": "wrap",
            "action.line_numbers": "lines",
            "action.zoom_in": "zoom_in",
            "action.zoom_out": "zoom_out",
            "action.zoom_reset": "zoom_reset",
            "action.fullscreen": "fullscreen",
            "action.exit": "exit",
            "action.about": "about",
        }
        for key, name in mapping.items():
            if key in self._actions:
                self._actions[key].setIcon(icon(name, c))

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
        self._menu_file.setTitle(t("menu.file", "File"))
        self._menu_edit.setTitle(t("menu.edit", "Edit"))
        self._menu_view.setTitle(t("menu.view", "View"))
        self._menu_syntax.setTitle(t("menu.syntax", "Syntax"))
        self._menu_themes.setTitle(t("menu.themes", "Themes"))
        self._menu_lang.setTitle(t("menu.ui_language", "UI Language"))
        self._menu_help.setTitle(t("menu.help", "Help"))
        self._sidebar_dock.setWindowTitle(t("panel.explorer", "Explorer"))
        labels = {
            "action.new": t("action.new", "New"),
            "action.open": t("action.open", "Open"),
            "action.open_folder": t("action.open_folder", "Open Folder…"),
            "action.save": t("action.save", "Save"),
            "action.save_as": t("action.save_as", "Save As"),
            "action.print": t("action.print", "Print…"),
            "action.export_pdf": t("action.export_pdf", "Export PDF…"),
            "action.find": t("action.find", "Find"),
            "action.replace": t("action.replace", "Replace"),
            "action.preview": t("action.preview", "Preview"),
            "action.toggle_sidebar": t("action.toggle_sidebar", "Toggle Explorer"),
            "action.word_wrap": t("action.word_wrap", "Word Wrap"),
            "action.line_numbers": t("action.line_numbers", "Line Numbers"),
            "action.zoom_in": t("action.zoom_in", "Zoom In"),
            "action.zoom_out": t("action.zoom_out", "Zoom Out"),
            "action.zoom_reset": t("action.zoom_reset", "Reset Zoom"),
            "action.fullscreen": t("action.fullscreen", "Full Screen"),
            "action.exit": t("action.exit", "Exit"),
            "action.about": t("action.about", "About"),
        }
        for key, label in labels.items():
            if key in self._actions:
                self._actions[key].setText(label)
                self._actions[key].setToolTip(label)
        tab = self.current_tab()
        if tab is not None:
            self._update_status_for(tab)
        else:
            self.setWindowTitle(t("app.name", "MagicEditor"))

    # --- session ------------------------------------------------------

    def _restore_session_files(self) -> bool:
        opened = False
        active_index = 0
        for path_str in self._session.open_files:
            path = Path(path_str)
            if not path.is_file():
                continue
            try:
                doc = open_document(path)
            except OSError:
                continue
            tab = self._add_document(doc, activate=False)
            if self._session.active_file and path_str == self._session.active_file:
                active_index = self.tabs.indexOf(tab)
            opened = True
        if opened:
            self.tabs.setCurrentIndex(max(0, active_index))
            w = self.current_tab()
            if w is not None:
                self._update_status_for(w)
        return opened

    def _collect_session(self) -> SessionState:
        open_files: list[str] = []
        active: str | None = None
        current = self.current_tab()
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, EditorTab) and w.document.path is not None:
                p = str(w.document.path.resolve())
                open_files.append(p)
                if w is current:
                    active = p
        return SessionState(
            theme=self._themes.current,
            language=self._tr.language,
            word_wrap=self._word_wrap,
            line_numbers=self._line_numbers,
            workspace=str(self._workspace) if self._workspace else None,
            open_files=open_files,
            active_file=active,
            geometry=self.saveGeometry(),
            window_state=self.saveState(),
        )

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
        light = theme_id == "clean_light"
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, EditorTab):
                w.set_syntax_light_theme(light)
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
        self._sidebar_dock.show()
        self._actions["action.toggle_sidebar"].setChecked(True)
        if persist:
            self._persist_session()

    def open_path(self, path: str | Path) -> None:
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
                return
        try:
            doc = open_document(path)
        except OSError as exc:
            QMessageBox.critical(self, "MagicEditor", str(exc))
            return
        self._add_document(doc)
        self._status.showMessage(f"Opened {path.name}", 3000)
        self._persist_session()

    def _add_document(self, doc: Document, *, activate: bool = True) -> EditorTab:
        tab = EditorTab(doc, self)
        tab.set_word_wrap(self._word_wrap)
        tab.set_line_numbers(self._line_numbers)
        tab.set_syntax_light_theme(self._themes.current == "clean_light")
        tab.modification_changed.connect(self._refresh_tab_titles)
        tab.cursor_info_changed.connect(self._status.set_cursor)
        tab.language_changed.connect(lambda _lang: self._sync_syntax_check())
        idx = self.tabs.addTab(tab, doc.display_name())
        if activate:
            self.tabs.setCurrentIndex(idx)
            self._update_status_for(tab)
            self._sync_syntax_check()
        return tab

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
        self._refresh_tab_titles()
        self._update_status_for(tab)
        self._persist_session()

    def show_find(self) -> None:
        tab = self.current_tab()
        if tab is None:
            return
        dlg = FindDialog(tab.editor, self, replace_mode=False)
        dlg.exec()

    def show_replace(self) -> None:
        tab = self.current_tab()
        if tab is None:
            return
        dlg = FindDialog(tab.editor, self, replace_mode=True)
        dlg.exec()

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

    def _close_tab(self, index: int) -> None:
        widget = self.tabs.widget(index)
        if isinstance(widget, EditorTab) and widget.document.modified:
            reply = QMessageBox.question(
                self,
                "MagicEditor",
                f"Save changes to {widget.document.title}?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
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

    def _on_tab_changed(self, index: int) -> None:
        w = self.tabs.widget(index)
        if isinstance(w, EditorTab):
            self._update_status_for(w)
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

    def _about(self) -> None:
        QMessageBox.about(
            self,
            "MagicEditor",
            "<h3>MagicEditor</h3>"
            "<p>Modern, fast text &amp; code editor for everyday work.</p>"
            "<p>Piece table · mmap-ready core · live preview · themes · i18n</p>"
            "<p>Version 0.1.0</p>",
        )

    def closeEvent(self, event: QCloseEvent | None) -> None:
        if event is None:
            return
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, EditorTab) and w.document.modified:
                reply = QMessageBox.question(
                    self,
                    "MagicEditor",
                    "There are unsaved documents. Quit anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply == QMessageBox.StandardButton.No:
                    event.ignore()
                    return
                break
        self._persist_session()
        event.accept()
