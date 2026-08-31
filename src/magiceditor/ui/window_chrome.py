"""Menus, actions, and toolbar for MainWindow (J1.2)."""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QAction, QActionGroup, QKeySequence
from PyQt6.QtWidgets import QLineEdit, QToolBar

from magiceditor.core.encoding import ENCODING_CATALOG
from magiceditor.core.syntax.detect import supported_languages

# (action_id, window method name, shortcut or None, checkable)
ACTION_SPECS: list[tuple[str, str, str | None, bool]] = [
    ("action.new", "new_document", "Ctrl+N", False),
    ("action.open", "open_file_dialog", "Ctrl+O", False),
    ("action.open_folder", "open_folder_dialog", "Ctrl+K", False),
    ("action.save", "save_current", "Ctrl+S", False),
    ("action.save_as", "save_current_as", "Ctrl+Shift+S", False),
    ("action.print", "print_current", "Ctrl+P", False),
    ("action.export_pdf", "export_pdf_current", "Ctrl+Shift+E", False),
    ("action.undo", "undo_current", "Ctrl+Z", False),
    ("action.redo", "redo_current", "Ctrl+Y", False),
    ("action.cut", "cut_current", "Ctrl+X", False),
    ("action.copy", "copy_current", "Ctrl+C", False),
    ("action.paste", "paste_current", "Ctrl+V", False),
    ("action.select_all", "select_all_current", "Ctrl+A", False),
    ("action.indent", "indent_current", "Ctrl+]", False),
    ("action.unindent", "unindent_current", "Ctrl+[", False),
    ("action.duplicate_line", "duplicate_line_current", "Ctrl+Shift+D", False),
    ("action.move_line_up", "move_line_up_current", "Alt+Up", False),
    ("action.move_line_down", "move_line_down_current", "Alt+Down", False),
    ("action.sort_lines", "sort_lines_current", None, False),
    ("action.join_lines", "join_lines_current", None, False),
    ("action.delete_blank_lines", "delete_blank_lines_current", None, False),
    ("action.trim_trailing", "trim_trailing_current", None, False),
    ("action.tabs_to_spaces", "tabs_to_spaces_current", None, False),
    ("action.spaces_to_tabs", "spaces_to_tabs_current", None, False),
    ("action.toggle_comment", "toggle_comment_current", "Ctrl+/", False),
    ("action.add_cursor_next", "multi_cursor_add_next", "Ctrl+D", False),
    ("action.select_all_occurrences", "multi_cursor_select_all", "Alt+F3", False),
    ("action.clear_cursors", "multi_cursor_clear", None, False),
    ("action.matching_brace", "goto_matching_brace", "Ctrl+M", False),
    ("action.find", "show_find", "Ctrl+F", False),
    ("action.replace", "show_replace", "Ctrl+H", False),
    ("action.find_in_files", "show_find_in_files", "Ctrl+Shift+F", False),
    ("action.goto_line", "show_goto_line", "Ctrl+G", False),
    ("action.goto_anything", "show_goto_anything", "Ctrl+P", False),
    ("action.toggle_bookmark", "toggle_bookmark", "Ctrl+F2", False),
    ("action.next_bookmark", "next_bookmark", "F2", False),
    ("action.prev_bookmark", "prev_bookmark", "Shift+F2", False),
    ("action.command_palette", "show_command_palette", "Ctrl+Shift+P", False),
    ("action.preview", "toggle_preview", "Ctrl+Shift+V", False),
    ("action.symbols", "show_symbol_list", "Ctrl+Shift+O", False),
    ("action.reload", "reload_current_from_disk", "F5", False),
    ("action.reveal_explorer", "reveal_in_explorer", None, False),
    ("action.copy_path", "copy_path_current", None, False),
    ("action.copy_dir", "copy_dir_current", None, False),
    ("action.compare", "compare_files_dialog", None, False),
    ("action.split_view", "toggle_split_view", None, False),
    ("action.toggle_spell", "toggle_spell_check", None, True),
    ("action.spell_ignore", "spell_ignore_word", None, False),
    ("action.spell_add", "spell_add_word", None, False),
    ("action.minimap", "toggle_minimap", None, True),
    ("action.performance", "show_performance_dashboard", None, False),
    ("action.live_browser", "open_live_preview_browser", None, False),
    ("action.cancel_search", "cancel_long_search", "Ctrl+Shift+C", False),
    ("action.export_theme", "export_theme_bundle", None, False),
    ("action.import_theme", "import_theme_bundle", None, False),
    ("action.toggle_sidebar", "toggle_sidebar", "Ctrl+B", True),
    ("action.word_wrap", "toggle_word_wrap", "Alt+Z", True),
    ("action.line_numbers", "toggle_line_numbers", None, True),
    ("action.zoom_in", "zoom_in", "Ctrl+=", False),
    ("action.zoom_out", "zoom_out", "Ctrl+-", False),
    ("action.zoom_reset", "zoom_reset", "Ctrl+0", False),
    ("action.fullscreen", "toggle_fullscreen", "F11", True),
    ("action.settings", "show_settings", "Ctrl+,", False),
    ("action.quick_open", "show_quick_open", "Ctrl+E", False),
    ("action.outline", "show_outline", "Ctrl+Shift+U", False),
    ("action.close_tab", "close_current_tab", "Ctrl+W", False),
    ("action.close_others", "close_other_tabs", None, False),
    ("action.close_all", "close_all_tabs", None, False),
    ("action.exit", "close", "Ctrl+Q", False),
]

FILE_MENU_KEYS = (
    "action.new",
    "action.open",
    "action.open_folder",
    "action.save",
    "action.save_as",
    "action.print",
    "action.export_pdf",
)
FILE_CLOSE_KEYS = ("action.close_tab", "action.close_others", "action.close_all")
EDIT_HISTORY_KEYS = ("action.undo", "action.redo")
EDIT_CLIP_KEYS = ("action.cut", "action.copy", "action.paste", "action.select_all")
EDIT_POWER_KEYS = (
    "action.indent",
    "action.unindent",
    "action.duplicate_line",
    "action.move_line_up",
    "action.move_line_down",
    "action.sort_lines",
    "action.join_lines",
    "action.delete_blank_lines",
    "action.trim_trailing",
    "action.tabs_to_spaces",
    "action.spaces_to_tabs",
    "action.toggle_comment",
    "action.add_cursor_next",
    "action.select_all_occurrences",
    "action.clear_cursors",
    "action.matching_brace",
)
EDIT_FIND_KEYS = (
    "action.find",
    "action.replace",
    "action.find_in_files",
    "action.goto_line",
    "action.goto_anything",
    "action.command_palette",
)
EDIT_MARK_KEYS = ("action.toggle_bookmark", "action.next_bookmark", "action.prev_bookmark")
VIEW_KEYS = (
    "action.preview",
    "action.toggle_sidebar",
    "action.quick_open",
    "action.outline",
    "action.symbols",
    "action.minimap",
    "action.split_view",
    "action.word_wrap",
    "action.line_numbers",
    "action.zoom_in",
    "action.zoom_out",
    "action.zoom_reset",
    "action.fullscreen",
    "action.settings",
)
TOOLS_KEYS = (
    "action.reload",
    "action.reveal_explorer",
    "action.copy_path",
    "action.copy_dir",
    "action.compare",
    "action.toggle_spell",
    "action.spell_ignore",
    "action.spell_add",
    "action.performance",
    "action.live_browser",
    "action.cancel_search",
    "action.export_theme",
    "action.import_theme",
)
TOOLBAR_FILE = ("action.new", "action.open", "action.open_folder", "action.save", "action.print")
TOOLBAR_HISTORY = ("action.undo", "action.redo")
TOOLBAR_CLIP = ("action.cut", "action.copy", "action.paste")
TOOLBAR_SEARCH = (
    "action.find",
    "action.replace",
    "action.find_in_files",
    "action.goto_line",
    "action.preview",
    "action.toggle_sidebar",
    "action.settings",
)


def action_ids() -> list[str]:
    return [spec[0] for spec in ACTION_SPECS]


ACTION_ICON_MAP: dict[str, str] = {
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
    "action.indent": "indent",
    "action.unindent": "unindent",
    "action.duplicate_line": "duplicate_line",
    "action.move_line_up": "move_up",
    "action.move_line_down": "move_down",
    "action.sort_lines": "sort",
    "action.join_lines": "join",
    "action.delete_blank_lines": "delete_lines",
    "action.trim_trailing": "trim",
    "action.tabs_to_spaces": "tabs_spaces",
    "action.spaces_to_tabs": "spaces_tabs",
    "action.toggle_comment": "comment",
    "action.add_cursor_next": "add_cursor",
    "action.select_all_occurrences": "select_occurrences",
    "action.clear_cursors": "clear_cursors",
    "action.matching_brace": "brace",
    "action.find": "find",
    "action.replace": "replace",
    "action.find_in_files": "find_files",
    "action.goto_line": "goto",
    "action.goto_anything": "goto_anything",
    "action.command_palette": "palette",
    "action.toggle_bookmark": "bookmark",
    "action.next_bookmark": "bookmark_next",
    "action.prev_bookmark": "bookmark_prev",
    "action.preview": "preview",
    "action.symbols": "symbols",
    "action.reload": "reload",
    "action.reveal_explorer": "reveal",
    "action.copy_path": "copy_path",
    "action.copy_dir": "copy_dir",
    "action.compare": "compare",
    "action.split_view": "split",
    "action.toggle_spell": "spell",
    "action.spell_ignore": "spell_ignore",
    "action.spell_add": "spell_add",
    "action.minimap": "minimap",
    "action.performance": "performance",
    "action.live_browser": "browser",
    "action.cancel_search": "cancel_search",
    "action.export_theme": "export_theme",
    "action.import_theme": "import_theme",
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
    "action.close_tab": "close_tab",
    "action.close_others": "close_others",
    "action.close_all": "close_all",
    "action.exit": "exit",
    "action.about": "about",
}


def populate_icons(window: Any) -> None:
    from magiceditor.ui.icons import icon, language_icon

    color = window._icon_color
    for key, name in ACTION_ICON_MAP.items():
        if key in window._actions:
            window._actions[key].setIcon(icon(name, color))
    for lang_id, action in window._syntax_actions.items():
        action.setIcon(language_icon(lang_id, color))
    for action in getattr(window, "_theme_actions", {}).values():
        action.setIcon(icon("theme", color))
    for action in getattr(window, "_lang_actions", {}).values():
        action.setIcon(icon("language", color))
    for menu, name in (
        (getattr(window, "_recent_menu", None), "recent"),
        (getattr(window, "_menu_encoding", None), "encoding"),
        (getattr(window, "_menu_eol", None), "eol"),
    ):
        if menu is not None:
            menu.setIcon(icon(name, color))
    enc_group = getattr(window, "_enc_group", None)
    if enc_group is not None:
        for action in enc_group.actions():
            action.setIcon(icon("encoding", color))
    eol_group = getattr(window, "_eol_group", None)
    if eol_group is not None:
        for action in eol_group.actions():
            action.setIcon(icon("eol", color))


def populate_actions(window: Any) -> None:
    for key, slot_name, shortcut, checkable in ACTION_SPECS:
        action = QAction(key, window)
        action.triggered.connect(getattr(window, slot_name))
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
            action.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
            action.setShortcutVisibleInContextMenu(True)
        action.setCheckable(checkable)
        action.setIconVisibleInMenu(True)
        window.addAction(action)
        window._actions[key] = action
    window._actions["action.redo"].setShortcuts(
        [QKeySequence("Ctrl+Y"), QKeySequence("Ctrl+Shift+Z")]
    )
    window._actions["action.word_wrap"].setChecked(window._word_wrap)
    window._actions["action.line_numbers"].setChecked(window._line_numbers)
    window._actions["action.toggle_sidebar"].setChecked(False)
    window._actions["action.toggle_spell"].setChecked(bool(window._session.spell_check))
    window._actions["action.minimap"].setChecked(bool(window._session.show_minimap))
    window._actions["action.print"].setShortcut(QKeySequence("Ctrl+P"))
    window._actions["action.goto_anything"].setShortcut(QKeySequence("Ctrl+Shift+G"))


def _add_keys(menu, window: Any, keys: tuple[str, ...]) -> None:
    for key in keys:
        menu.addAction(window._actions[key])


def populate_menus(window: Any) -> None:
    mb = window.menuBar()
    mb.setNativeMenuBar(False)
    window._menu_file = mb.addMenu("&Arquivo")
    window._menu_edit = mb.addMenu("&Editar")
    window._menu_view = mb.addMenu("E&xibir")
    window._menu_format = mb.addMenu("&Formatar")
    window._menu_tools = mb.addMenu("&Ferramentas")
    window._menu_syntax = mb.addMenu("&Sintaxe")
    window._menu_themes = mb.addMenu("&Temas")
    window._menu_lang = mb.addMenu("&Idioma")
    window._menu_help = mb.addMenu("A&juda")

    _add_keys(window._menu_file, window, FILE_MENU_KEYS)
    window._menu_file.addSeparator()
    _add_keys(window._menu_file, window, FILE_CLOSE_KEYS)
    window._menu_file.addSeparator()
    window._recent_menu = window._menu_file.addMenu(
        window._tr.t("menu.recent", "Arquivos recentes")
    )
    window._rebuild_recent_menu()
    window._menu_file.addSeparator()
    window._menu_file.addAction(window._actions["action.exit"])

    _add_keys(window._menu_edit, window, EDIT_HISTORY_KEYS)
    window._menu_edit.addSeparator()
    _add_keys(window._menu_edit, window, EDIT_CLIP_KEYS)
    window._menu_edit.addSeparator()
    _add_keys(window._menu_edit, window, EDIT_POWER_KEYS)
    window._menu_edit.addSeparator()
    _add_keys(window._menu_edit, window, EDIT_FIND_KEYS)
    window._menu_edit.addSeparator()
    _add_keys(window._menu_edit, window, EDIT_MARK_KEYS)
    _add_keys(window._menu_view, window, VIEW_KEYS)
    _add_keys(window._menu_tools, window, TOOLS_KEYS)

    window._menu_encoding = window._menu_format.addMenu(
        window._tr.t("menu.encoding", "Codificação")
    )
    window._enc_group = QActionGroup(window)
    window._enc_group.setExclusive(True)
    for enc, label in ENCODING_CATALOG:
        a = QAction(label, window)
        a.setCheckable(True)
        a.setData(enc)
        a.triggered.connect(lambda checked=False, e=enc: window.set_current_encoding(e))
        window._enc_group.addAction(a)
        window._menu_encoding.addAction(a)
    window._menu_eol = window._menu_format.addMenu(window._tr.t("menu.eol", "Fim de linha"))
    window._eol_group = QActionGroup(window)
    window._eol_group.setExclusive(True)
    for eol, label in (
        ("LF", "Unix (LF)"),
        ("CRLF", "Windows (CRLF)"),
        ("CR", "Classic Mac (CR)"),
    ):
        a = QAction(label, window)
        a.setCheckable(True)
        a.setData(eol)
        a.triggered.connect(lambda checked=False, e=eol: window.set_current_eol(e))
        window._eol_group.addAction(a)
        window._menu_eol.addAction(a)

    for lang_id, label in supported_languages():
        action = QAction(label, window)
        action.setCheckable(True)
        action.setData(lang_id)
        action.triggered.connect(lambda checked=False, lid=lang_id: window.set_syntax_language(lid))
        window._syntax_group.addAction(action)
        window._menu_syntax.addAction(action)
        window._syntax_actions[lang_id] = action

    for theme_id, label in window._themes.list_themes():
        action = QAction(label, window)
        action.setCheckable(True)
        action.setData(theme_id)
        action.triggered.connect(
            lambda checked=False, t=theme_id: window.apply_theme(t, persist=True)
        )
        window._theme_group.addAction(action)
        window._menu_themes.addAction(action)
        window._theme_actions[theme_id] = action

    for lang in window._tr.available_languages() or ["en_US", "pt_BR"]:
        action = QAction(lang, window)
        action.setCheckable(True)
        action.setData(lang)
        action.triggered.connect(
            lambda checked=False, code=lang: window._set_language(code, persist=True)
        )
        window._lang_group.addAction(action)
        window._menu_lang.addAction(action)
        window._lang_actions[lang] = action

    about = QAction("About", window)
    about.setObjectName("action.about")
    about.triggered.connect(window._about)
    window._actions["action.about"] = about
    window._menu_help.addAction(about)


def populate_toolbar(window: Any) -> None:
    tb = QToolBar("Main", window)
    tb.setObjectName("mainToolbar")
    tb.setMovable(False)
    tb.setIconSize(QSize(22, 22))
    tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
    window._toolbar = tb
    window.addToolBar(tb)
    _add_keys(tb, window, TOOLBAR_FILE)
    tb.addSeparator()
    _add_keys(tb, window, TOOLBAR_HISTORY)
    tb.addSeparator()
    _add_keys(tb, window, TOOLBAR_CLIP)
    tb.addSeparator()
    _add_keys(tb, window, TOOLBAR_SEARCH)
    tb.addSeparator()
    search = QLineEdit(window)
    search.setObjectName("toolbarSearch")
    search.setPlaceholderText("Pesquisar arquivos (Ctrl+E)")
    search.setClearButtonEnabled(True)
    search.setMinimumWidth(200)
    search.setMaximumWidth(320)
    search.setReadOnly(True)
    search.setCursor(Qt.CursorShape.PointingHandCursor)
    search.installEventFilter(window)
    tb.addWidget(search)
    window._quick_search = search
