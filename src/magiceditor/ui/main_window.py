"""Primary application window — modern daily-driver editor chrome."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QCloseEvent, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QDockWidget,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QStyle,
    QToolBar,
    QWidget,
)

from magiceditor.i18n.translator import TranslatorManager
from magiceditor.services.document import Document
from magiceditor.services.document_io import open_document, save_document
from magiceditor.themes.manager import ThemeManager
from magiceditor.ui.editor_tab import EditorTab
from magiceditor.ui.sidebar import Sidebar
from magiceditor.ui.status_bar import EditorStatusBar
from magiceditor.ui.tab_manager import TabManager


class MainWindow(QMainWindow):
    def __init__(
        self,
        translator: TranslatorManager | None = None,
        themes: ThemeManager | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._tr = translator or TranslatorManager()
        self._themes = themes or ThemeManager()
        self._untitled_seq = 1
        self._word_wrap = False
        self._line_numbers = True

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
        self._sidebar.file_activated.connect(self.open_path)

        self._actions: dict[str, QAction] = {}
        self._build_actions()
        self._build_menus()
        self._build_toolbar()

        self._tr.language_changed.connect(self.retranslate_ui)
        try:
            if self._tr.language not in self._tr.available_languages():
                self._tr.load("en_US")
            elif not self._tr.available_languages():
                pass
            else:
                self._tr.load(self._tr.language)
        except OSError:
            try:
                self._tr.load("en_US")
            except OSError:
                pass

        self.new_document()
        self.retranslate_ui()

    def _icon(self, standard: QStyle.StandardPixmap):
        style = self.style()
        return style.standardIcon(standard) if style else None

    def _build_actions(self) -> None:
        def act(
            key: str,
            slot,
            shortcut: str | None = None,
            icon: QStyle.StandardPixmap | None = None,
        ) -> QAction:
            action = QAction(key, self)
            action.triggered.connect(slot)
            if shortcut:
                action.setShortcut(QKeySequence(shortcut))
            if icon is not None:
                ic = self._icon(icon)
                if ic is not None:
                    action.setIcon(ic)
            self._actions[key] = action
            return action

        SP = QStyle.StandardPixmap
        act("action.new", self.new_document, "Ctrl+N", SP.SP_FileIcon)
        act("action.open", self.open_file_dialog, "Ctrl+O", SP.SP_DialogOpenButton)
        act("action.save", self.save_current, "Ctrl+S", SP.SP_DialogSaveButton)
        act("action.save_as", self.save_current_as, "Ctrl+Shift+S")
        act("action.find", self.show_find, "Ctrl+F", SP.SP_FileDialogContentsView)
        act("action.replace", self.show_replace, "Ctrl+H")
        act("action.preview", self.toggle_preview, "Ctrl+Shift+P")
        act("action.toggle_sidebar", self.toggle_sidebar, "Ctrl+B")
        act("action.word_wrap", self.toggle_word_wrap, "Alt+Z")
        act("action.line_numbers", self.toggle_line_numbers)
        act("action.zoom_in", self.zoom_in, "Ctrl+=")
        act("action.zoom_out", self.zoom_out, "Ctrl+-")
        act("action.zoom_reset", self.zoom_reset, "Ctrl+0")
        act("action.fullscreen", self.toggle_fullscreen, "F11")
        act("action.exit", self.close, "Ctrl+Q")

    def _build_menus(self) -> None:
        mb = self.menuBar()
        self._menu_file = mb.addMenu("File")
        self._menu_edit = mb.addMenu("Edit")
        self._menu_view = mb.addMenu("View")
        self._menu_themes = mb.addMenu("Themes")
        self._menu_lang = mb.addMenu("Language")
        self._menu_help = mb.addMenu("Help")

        for key in ("action.new", "action.open", "action.save", "action.save_as"):
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

        for theme_id, label in self._themes.list_themes():
            action = QAction(label, self)
            action.triggered.connect(lambda checked=False, t=theme_id: self.apply_theme(t))
            self._menu_themes.addAction(action)

        for lang in self._tr.available_languages() or ["en_US", "pt_BR"]:
            action = QAction(lang, self)
            action.triggered.connect(
                lambda checked=False, code=lang: self._set_language(code)
            )
            self._menu_lang.addAction(action)

        about = QAction("About", self)
        about.triggered.connect(self._about)
        self._menu_help.addAction(about)

    def _build_toolbar(self) -> None:
        tb = QToolBar("Main", self)
        tb.setObjectName("mainToolbar")
        tb.setMovable(False)
        tb.setIconSize(tb.iconSize())
        self.addToolBar(tb)
        for key in (
            "action.new",
            "action.open",
            "action.save",
            "action.find",
            "action.preview",
            "action.toggle_sidebar",
        ):
            tb.addAction(self._actions[key])

    def retranslate_ui(self) -> None:
        t = self._tr.t
        self._menu_file.setTitle(t("menu.file", "File"))
        self._menu_edit.setTitle(t("menu.edit", "Edit"))
        self._menu_view.setTitle(t("menu.view", "View"))
        self._menu_themes.setTitle(t("menu.themes", "Themes"))
        self._menu_lang.setTitle(t("menu.language", "Language"))
        self._menu_help.setTitle(t("menu.help", "Help"))
        self._sidebar_dock.setWindowTitle(t("panel.explorer", "Explorer"))
        labels = {
            "action.new": t("action.new", "New"),
            "action.open": t("action.open", "Open"),
            "action.save": t("action.save", "Save"),
            "action.save_as": t("action.save_as", "Save As"),
            "action.find": t("action.find", "Find"),
            "action.replace": t("action.replace", "Replace"),
            "action.preview": t("action.preview", "Preview"),
            "action.toggle_sidebar": t("action.toggle_sidebar", "Toggle Sidebar"),
            "action.word_wrap": t("action.word_wrap", "Word Wrap"),
            "action.line_numbers": t("action.line_numbers", "Line Numbers"),
            "action.zoom_in": t("action.zoom_in", "Zoom In"),
            "action.zoom_out": t("action.zoom_out", "Zoom Out"),
            "action.zoom_reset": t("action.zoom_reset", "Reset Zoom"),
            "action.fullscreen": t("action.fullscreen", "Full Screen"),
            "action.exit": t("action.exit", "Exit"),
        }
        for key, label in labels.items():
            if key in self._actions:
                self._actions[key].setText(label)
        tab = self.current_tab()
        if tab is not None:
            self._update_status_for(tab)
        else:
            self.setWindowTitle(t("app.name", "MagicEditor"))

    def apply_theme(self, theme_id: str) -> None:
        qapp = QApplication.instance()
        if qapp is not None:
            self._themes.apply(qapp, theme_id)
            self._status.showMessage(f"Theme: {theme_id}", 2500)

    def _set_language(self, lang: str) -> None:
        self._tr.load(lang)

    def current_tab(self) -> EditorTab | None:
        w = self.tabs.currentWidget()
        return w if isinstance(w, EditorTab) else None

    def new_document(self) -> EditorTab:
        title = f"Untitled-{self._untitled_seq}"
        self._untitled_seq += 1
        return self._add_document(Document.blank(title=title))

    def open_file_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            self._tr.t("action.open", "Open"),
            str(Path.home()),
            "Text (*.txt *.md *.py *.json *.xml *.html *.css *.js *.sql *.log);;All (*.*)",
        )
        if path:
            self.open_path(path)

    def open_path(self, path: str | Path) -> None:
        path = Path(path)
        try:
            doc = open_document(path)
        except OSError as exc:
            QMessageBox.critical(self, "MagicEditor", str(exc))
            return
        self._add_document(doc)
        self._sidebar.set_root_path(path.parent)
        self._status.showMessage(f"Opened {path.name}", 3000)

    def _add_document(self, doc: Document) -> EditorTab:
        tab = EditorTab(doc, self)
        tab.set_word_wrap(self._word_wrap)
        tab.set_line_numbers(self._line_numbers)
        tab.modification_changed.connect(self._refresh_tab_titles)
        tab.cursor_info_changed.connect(self._status.set_cursor)
        idx = self.tabs.addTab(tab, doc.display_name())
        self.tabs.setCurrentIndex(idx)
        self._update_status_for(tab)
        return tab

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
        tab.editor.document().setModified(False)
        self._refresh_tab_titles()
        self._update_status_for(tab)
        self._status.showMessage("Saved", 2000)

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
        tab.editor.document().setModified(False)
        self._refresh_tab_titles()
        self._update_status_for(tab)

    def show_find(self) -> None:
        tab = self.current_tab()
        if tab is not None:
            tab.show_find(replace=False)

    def show_replace(self) -> None:
        tab = self.current_tab()
        if tab is not None:
            tab.show_find(replace=True)

    def toggle_preview(self) -> None:
        tab = self.current_tab()
        if tab is not None:
            on = tab.toggle_preview()
            self._status.showMessage("Preview on" if on else "Preview off", 2000)

    def toggle_sidebar(self) -> None:
        self._sidebar_dock.setVisible(not self._sidebar_dock.isVisible())

    def toggle_word_wrap(self) -> None:
        self._word_wrap = not self._word_wrap
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, EditorTab):
                w.set_word_wrap(self._word_wrap)
        self._status.showMessage("Word wrap on" if self._word_wrap else "Word wrap off", 2000)

    def toggle_line_numbers(self) -> None:
        self._line_numbers = not self._line_numbers
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, EditorTab):
                w.set_line_numbers(self._line_numbers)

    def zoom_in(self) -> None:
        tab = self.current_tab()
        if tab is not None:
            tab.editor.zoom_in_one()

    def zoom_out(self) -> None:
        tab = self.current_tab()
        if tab is not None:
            tab.editor.zoom_out_one()

    def zoom_reset(self) -> None:
        tab = self.current_tab()
        if tab is not None:
            tab.editor.reset_zoom()

    def toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

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

    def _update_status_for(self, tab: EditorTab) -> None:
        doc = tab.document
        self._status.set_encoding(doc.encoding)
        self._status.set_eol(doc.eol)
        suffix = Path(doc.title).suffix.lower().lstrip(".") or "text"
        self._status.set_filetype(suffix.upper())
        self.setWindowTitle(f"{doc.display_name()} — MagicEditor")

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
        event.accept()
