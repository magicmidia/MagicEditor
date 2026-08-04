"""Mixin: roadmap power features wired into MainWindow (B-H).

Keeps main_window thinner; methods expect MainWindow attributes
(``tabs``, ``_tr``, ``_session``, ``_status``, etc.).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QFileSystemWatcher, QPoint, Qt, QTimer, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QApplication,
    QDockWidget,
    QFileDialog,
    QInputDialog,
    QMessageBox,
    QPlainTextEdit,
)

from magiceditor.core.brace_match import brace_at_or_near, find_matching_brace
from magiceditor.core.comment_rules import toggle_line_comments
from magiceditor.core.document_edit import (
    read_lines,
    replace_line_range,
    selection_or_all,
)
from magiceditor.core.line_ops import (
    delete_blank_lines,
    join_lines,
    move_line_down,
    move_line_up,
    sort_lines,
    spaces_to_tabs,
    tabs_to_spaces,
    trim_trailing_whitespace,
)
from magiceditor.core.multi_cursor import (
    find_all_occurrences,
    find_next_occurrence,
    word_at,
)
from magiceditor.core.spell import (
    SUPPORTED_SPELL_LANGS,
    SpellEngine,
    spell_enabled_for_language,
)
from magiceditor.core.symbols import extract_symbols
from magiceditor.services.document_io import open_document, save_document
from magiceditor.services.performance_info import document_mmap_active, snapshot_for_document
from magiceditor.services.portable import is_portable_mode
from magiceditor.ui.command_palette import CommandPaletteDialog, PaletteCommand
from magiceditor.ui.compare_dialog import CompareDialog
from magiceditor.ui.editor_context_menu import build_editor_context_menu
from magiceditor.ui.goto_anything import GotoAnythingDialog
from magiceditor.ui.performance_dialog import PerformanceDialog
from magiceditor.ui.virtual_editor import VirtualEditor

if TYPE_CHECKING:
    from magiceditor.ui.editor_tab import EditorTab


class PowerFeaturesMixin:
    """Expects to be mixed into MainWindow."""

    _spell_engine: SpellEngine
    _file_watcher: QFileSystemWatcher
    _autosave_timer: QTimer
    _search_cancel_flag: bool
    _minimap_enabled: bool
    _split_secondary: Any

    def _init_power_features(self) -> None:
        session = self._session  # type: ignore[attr-defined]
        lang = getattr(session, "spell_language", None) or session.language or "pt_BR"
        self._spell_engine = SpellEngine(language=lang)
        self._spell_engines: dict[frozenset[str], SpellEngine] = {
            frozenset(self._spell_engine.active_languages()): self._spell_engine
        }
        self._file_watcher = QFileSystemWatcher(self)  # type: ignore[arg-type]
        self._file_watcher.fileChanged.connect(self._on_disk_file_changed)
        self._autosave_timer = QTimer(self)  # type: ignore[arg-type]
        self._autosave_timer.timeout.connect(self._autosave_tick)
        self._search_cancel_flag = False
        self._minimap_enabled = bool(getattr(session, "show_minimap", False))
        self._split_secondary = None
        self._apply_autosave_interval()
        self._sync_spell_to_editors()
        self.apply_minimap_to_tabs()

    def _apply_autosave_interval(self) -> None:
        sec = int(getattr(self._session, "autosave_interval_sec", 0) or 0)  # type: ignore[attr-defined]
        if sec > 0:
            self._autosave_timer.start(sec * 1000)
        else:
            self._autosave_timer.stop()

    def _autosave_tick(self) -> None:
        tabs = self.tabs  # type: ignore[attr-defined]
        for i in range(tabs.count()):
            w = tabs.widget(i)
            if w is None:
                continue
            doc = w.document
            if doc.path is not None and doc.modified:
                try:
                    save_document(doc)
                    doc.modified = False
                    w.modification_changed.emit()
                except OSError:
                    pass

    def _current_tab(self) -> EditorTab | None:
        return self.current_tab()  # type: ignore[attr-defined, no-any-return]

    def _current_doc(self):
        tab = self._current_tab()
        return tab.document if tab else None

    def _sel_line_range(self) -> tuple[int | None, int | None]:
        tab = self._current_tab()
        if tab is None:
            return None, None
        ed = tab.editor
        if isinstance(ed, VirtualEditor) and ed.has_selection():
            s_line, _sc, e_line, _ec = ed._normalized_selection()
            return s_line, e_line
        return None, None

    def _apply_line_transform(self, transform) -> None:
        tab = self._current_tab()
        if tab is None:
            return
        doc = tab.document
        a, b = self._sel_line_range()
        selection_or_all(doc, sel_start_line=a, sel_end_line=b, transform=transform)
        self._refresh_editor_after_doc_edit(tab)

    def _refresh_editor_after_doc_edit(self, tab: EditorTab) -> None:
        ed = tab.editor
        if isinstance(ed, VirtualEditor):
            ed._update_scrollbars()
            ed.viewport().update()
            ed.textChanged.emit()
            ed.modificationChanged.emit(True)
        else:
            # classic QPlainTextEdit

            cur = ed.textCursor()
            pos = cur.position()
            ed.setPlainText(tab.document.text())
            cur = ed.textCursor()
            cur.setPosition(min(pos, len(ed.toPlainText())))
            ed.setTextCursor(cur)
        tab.document.mark_modified()
        tab.modification_changed.emit()

    # --- B: line ops -------------------------------------------------

    def move_line_up_current(self) -> None:
        tab = self._current_tab()
        if tab is None:
            return
        ed = tab.editor
        if isinstance(ed, VirtualEditor):
            line = ed._cursor_line
            lines = read_lines(tab.document)
            new_lines, new_i = move_line_up(lines, line)
            replace_line_range(tab.document, 0, len(lines), new_lines)
            ed._cursor_line = new_i
            self._refresh_editor_after_doc_edit(tab)

    def move_line_down_current(self) -> None:
        tab = self._current_tab()
        if tab is None:
            return
        ed = tab.editor
        if isinstance(ed, VirtualEditor):
            line = ed._cursor_line
            lines = read_lines(tab.document)
            new_lines, new_i = move_line_down(lines, line)
            replace_line_range(tab.document, 0, len(lines), new_lines)
            ed._cursor_line = new_i
            self._refresh_editor_after_doc_edit(tab)

    def sort_lines_current(self) -> None:
        self._apply_line_transform(sort_lines)

    def join_lines_current(self) -> None:
        self._apply_line_transform(join_lines)

    def delete_blank_lines_current(self) -> None:
        self._apply_line_transform(delete_blank_lines)

    def trim_trailing_current(self) -> None:
        self._apply_line_transform(trim_trailing_whitespace)

    def tabs_to_spaces_current(self) -> None:
        w = int(getattr(self._session, "tab_width", 4) or 4)  # type: ignore[attr-defined]
        self._apply_line_transform(lambda ls: tabs_to_spaces(ls, w))

    def spaces_to_tabs_current(self) -> None:
        w = int(getattr(self._session, "tab_width", 4) or 4)  # type: ignore[attr-defined]
        self._apply_line_transform(lambda ls: spaces_to_tabs(ls, w))

    def toggle_comment_current(self) -> None:
        tab = self._current_tab()
        if tab is None:
            return
        lang = tab.language

        def transform(ls: list[str]) -> list[str]:
            return toggle_line_comments(ls, lang)

        self._apply_line_transform(transform)

    def multi_cursor_add_next(self) -> None:
        tab = self._current_tab()
        if tab is None or not isinstance(tab.editor, VirtualEditor):
            return
        ed: VirtualEditor = tab.editor
        lines = read_lines(tab.document)
        if ed.has_selection():
            needle = ed.selected_text()
            if "\n" in needle:
                return
        else:
            w = word_at(lines, ed._cursor_line, ed._cursor_col)
            if w is None:
                return
            needle, start, end = w
            ed._anchor_line = ed._cursor_line
            ed._anchor_col = start
            ed._cursor_col = end
        extra = getattr(ed, "_extra_cursors", None)
        if extra is None:
            ed._extra_cursors = []  # type: ignore[attr-defined]
            extra = ed._extra_cursors  # type: ignore[attr-defined]
        after_line = ed._cursor_line
        after_col = ed._cursor_col
        nxt = find_next_occurrence(
            lines, needle, after_line=after_line, after_col=after_col, wrap=True
        )
        if nxt is None:
            return
        # avoid duplicate
        pos = (nxt.line, nxt.col)
        if pos not in [(c[0], c[1]) for c in extra] and pos != (
            ed._cursor_line,
            ed._anchor_col if ed.has_selection() else ed._cursor_col,
        ):
            extra.append((nxt.line, nxt.col, nxt.col + len(needle)))
        ed._cursor_line = nxt.line
        ed._anchor_line = nxt.line
        ed._anchor_col = nxt.col
        ed._cursor_col = nxt.col + len(needle)
        ed._ensure_visible(nxt.line)
        ed.cursorPositionChanged.emit()
        ed.viewport().update()
        self._update_status_extras()

    def multi_cursor_select_all(self) -> None:
        tab = self._current_tab()
        if tab is None or not isinstance(tab.editor, VirtualEditor):
            return
        ed = tab.editor
        lines = read_lines(tab.document)
        if ed.has_selection():
            needle = ed.selected_text()
        else:
            w = word_at(lines, ed._cursor_line, ed._cursor_col)
            if w is None:
                return
            needle = w[0]
        hits = find_all_occurrences(lines, needle, max_hits=200)
        ed._extra_cursors = [  # type: ignore[attr-defined]
            (h.line, h.col, h.col + len(needle)) for h in hits
        ]
        if hits:
            h0 = hits[0]
            ed._cursor_line = h0.line
            ed._anchor_line = h0.line
            ed._anchor_col = h0.col
            ed._cursor_col = h0.col + len(needle)
        ed.viewport().update()
        self._update_status_extras()

    def multi_cursor_clear(self) -> None:
        tab = self._current_tab()
        if tab is None or not isinstance(tab.editor, VirtualEditor):
            return
        ed = tab.editor
        ed._extra_cursors = []  # type: ignore[attr-defined]
        ed.viewport().update()
        self._update_status_extras()

    def goto_matching_brace(self) -> None:
        tab = self._current_tab()
        if tab is None or not isinstance(tab.editor, VirtualEditor):
            return
        ed = tab.editor
        # search nearby lines window
        start = max(0, ed._cursor_line - 200)
        end = min(tab.document.line_index().line_count, ed._cursor_line + 200)
        chunk_lines = read_lines(tab.document, start, end)
        chunk = "\n".join(chunk_lines)
        # offset of cursor within chunk
        off = 0
        for i in range(ed._cursor_line - start):
            off += len(chunk_lines[i]) + 1
        off += ed._cursor_col
        bpos = brace_at_or_near(chunk, off)
        if bpos is None:
            return
        match = find_matching_brace(chunk, bpos)
        if match is None:
            return
        # map match back to line/col
        line = start
        col = 0
        pos = 0
        for ln in chunk_lines:
            if pos + len(ln) >= match:
                col = match - pos
                ed.goto_line(line, col)
                return
            pos += len(ln) + 1
            line += 1

    # --- C: navigation -----------------------------------------------

    def show_command_palette(self) -> None:
        tr = self._tr  # type: ignore[attr-defined]
        actions = self._actions  # type: ignore[attr-defined]
        cmds: list[PaletteCommand] = []
        for key, act in actions.items():
            label = act.text() or key
            sc = act.shortcut().toString() if act.shortcut() else ""
            cmds.append(
                PaletteCommand(
                    id=key,
                    label=label.replace("&", ""),
                    callback=act.trigger,
                    shortcut=sc,
                )
            )
        # extras
        cmds.append(
            PaletteCommand(
                "palette.performance",
                tr.t("action.performance", "Performance dashboard"),
                self.show_performance_dashboard,
            )
        )
        dlg = CommandPaletteDialog(
            cmds,
            self,  # type: ignore[arg-type]
            title=tr.t("palette.title", "Command Palette"),
            placeholder=tr.t("palette.placeholder", "Type a command…"),
        )
        if dlg.exec():
            cmd = dlg.selected_command()
            if cmd is not None:
                cmd.callback()

    def show_goto_anything(self) -> None:
        session = self._session  # type: ignore[attr-defined]
        files = list(session.recent_files)
        for i in range(self.tabs.count()):  # type: ignore[attr-defined]
            w = self.tabs.widget(i)  # type: ignore[attr-defined]
            if w and w.document.path:
                files.append(str(w.document.path))
        symbols: list[tuple[str, int]] = []
        tab = self._current_tab()
        if tab is not None:
            text = tab.document.text() if len(tab.document.buffer) < 2_000_000 else ""
            if text:
                for s in extract_symbols(text, tab.language):
                    symbols.append((s.name, s.line))
        dlg = GotoAnythingDialog(files=files, symbols=symbols, parent=self)  # type: ignore[arg-type]
        if dlg.exec():
            tgt = dlg.chosen()
            if tgt is None:
                return
            if tgt.kind == "file" and tgt.path:
                self.open_path(tgt.path)  # type: ignore[attr-defined]
            elif tgt.kind == "line" and tgt.line:
                if tgt.path:
                    self.open_path(tgt.path)  # type: ignore[attr-defined]
                tab = self._current_tab()
                if tab:
                    tab.goto_line(tgt.line, 1)
            elif tgt.kind == "symbol" and tgt.line:
                tab = self._current_tab()
                if tab:
                    tab.goto_line(tgt.line, 1)

    def show_symbol_list(self) -> None:
        tab = self._current_tab()
        if tab is None:
            return
        text = tab.document.text() if len(tab.document.buffer) < 2_000_000 else ""
        syms = extract_symbols(text, tab.language) if text else []
        if not syms:
            QMessageBox.information(
                self,  # type: ignore[arg-type]
                "Symbols",
                self._tr.t("symbols.empty", "No symbols found for this language."),  # type: ignore[attr-defined]
            )
            return
        labels = [f"{s.kind}: {s.name}  (:{s.line})" for s in syms]
        item, ok = QInputDialog.getItem(
            self,  # type: ignore[arg-type]
            self._tr.t("symbols.title", "Symbols"),  # type: ignore[attr-defined]
            self._tr.t("symbols.pick", "Go to symbol:"),  # type: ignore[attr-defined]
            labels,
            0,
            False,
        )
        if ok and item:
            idx = labels.index(item)
            tab.goto_line(syms[idx].line, 1)

    def reload_current_from_disk(self) -> None:
        tab = self._current_tab()
        if tab is None or tab.document.path is None:
            return
        path = tab.document.path
        if tab.document.modified:
            r = QMessageBox.question(
                self,  # type: ignore[arg-type]
                self._tr.t("reload.title", "Reload"),  # type: ignore[attr-defined]
                self._tr.t(
                    "reload.dirty",
                    "File has unsaved changes. Reload and discard?",
                ),  # type: ignore[attr-defined]
            )
            if r != QMessageBox.StandardButton.Yes:
                return
        try:
            new_doc = open_document(path)
        except OSError as exc:
            QMessageBox.warning(self, "Reload", str(exc))  # type: ignore[arg-type]
            return
        # replace tab content by reopening
        idx = self.tabs.currentIndex()  # type: ignore[attr-defined]
        self.tabs.tabCloseRequested.emit(idx)  # type: ignore[attr-defined]
        self.open_path(str(path))  # type: ignore[attr-defined]
        _ = new_doc

    def _on_disk_file_changed(self, path: str) -> None:
        tab = self._current_tab()
        if tab is None or tab.document.path is None:
            return
        if normalize_paths_equal(str(tab.document.path), path):
            self._status.set_sync_message(  # type: ignore[attr-defined]
                self._tr.t("status.file_changed", "File changed on disk — reload?")  # type: ignore[attr-defined]
            )

    def watch_path(self, path: str | None) -> None:
        files = self._file_watcher.files()
        if files:
            self._file_watcher.removePaths(files)
        if path and Path(path).is_file():
            self._file_watcher.addPath(path)

    def toggle_minimap(self) -> None:
        self._minimap_enabled = not self._minimap_enabled
        self._session.show_minimap = self._minimap_enabled  # type: ignore[attr-defined]
        for i in range(self.tabs.count()):  # type: ignore[attr-defined]
            w = self.tabs.widget(i)  # type: ignore[attr-defined]
            if w is not None and hasattr(w, "set_minimap_visible"):
                w.set_minimap_visible(self._minimap_enabled)
        if "action.minimap" in self._actions:  # type: ignore[attr-defined]
            self._actions["action.minimap"].setChecked(self._minimap_enabled)  # type: ignore[attr-defined]
        self._status.set_sync_message(  # type: ignore[attr-defined]
            f"Minimap: {'on' if self._minimap_enabled else 'off'}"
        )
        self._persist_session()  # type: ignore[attr-defined]

    def apply_minimap_to_tabs(self) -> None:
        enabled = bool(getattr(self._session, "show_minimap", False))  # type: ignore[attr-defined]
        self._minimap_enabled = enabled
        for i in range(self.tabs.count()):  # type: ignore[attr-defined]
            w = self.tabs.widget(i)  # type: ignore[attr-defined]
            if w is not None and hasattr(w, "set_minimap_visible"):
                w.set_minimap_visible(enabled)

    # --- D: workspace ------------------------------------------------

    def reveal_in_explorer(self) -> None:
        tab = self._current_tab()
        if tab is None or tab.document.path is None:
            return
        path = Path(tab.document.path)
        folder = path.parent
        if sys.platform == "win32":
            subprocess.run(["explorer", "/select,", str(path)], check=False)
        else:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def copy_path_current(self) -> None:
        tab = self._current_tab()
        if tab is None or tab.document.path is None:
            return
        QApplication.clipboard().setText(str(tab.document.path))

    def copy_dir_current(self) -> None:
        tab = self._current_tab()
        if tab is None or tab.document.path is None:
            return
        QApplication.clipboard().setText(str(Path(tab.document.path).parent))

    def compare_files_dialog(self) -> None:
        left, _ = QFileDialog.getOpenFileName(self, "Left file")  # type: ignore[arg-type]
        if not left:
            return
        right, _ = QFileDialog.getOpenFileName(self, "Right file")  # type: ignore[arg-type]
        if not right:
            return
        dlg = CompareDialog.from_paths(Path(left), Path(right), self)  # type: ignore[arg-type]
        dlg.exec()

    def toggle_split_view(self) -> None:
        # Simple: open second pane using a dock with same tab text snapshot
        tab = self._current_tab()
        if tab is None:
            return
        if self._split_secondary is not None:
            self.removeDockWidget(self._split_secondary)  # type: ignore[attr-defined]
            self._split_secondary = None
            return
        dock = QDockWidget(
            self._tr.t("split.title", "Split view"),
            self,  # type: ignore[attr-defined]
        )
        view = QPlainTextEdit(dock)
        if len(tab.document.buffer) < 5_000_000:
            text = tab.document.text()
        else:
            text = "(huge file - use main pane)"
        view.setPlainText(text[:2_000_000])
        view.setReadOnly(True)
        dock.setWidget(view)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)  # type: ignore[attr-defined]
        self._split_secondary = dock

    # --- G: spell ----------------------------------------------------

    def _spell_langs_for_tab(self, tab: EditorTab) -> list[str]:
        session = self._session  # type: ignore[attr-defined]
        if getattr(tab, "spell_languages", None):
            return list(tab.spell_languages)
        primary = getattr(session, "spell_language", None) or "pt_BR"
        if primary not in SUPPORTED_SPELL_LANGS:
            primary = "pt_BR"
        langs = [primary]
        extra = (getattr(session, "spell_extra_languages", "") or "").replace(" ", "")
        for code in extra.split(","):
            if code in SUPPORTED_SPELL_LANGS and code not in langs:
                langs.append(code)
        return langs

    def _wire_editor_context_menu(self, editor: VirtualEditor) -> None:
        """Connect VirtualEditor.context_menu_requested → popup QMenu.

        Menu is triggered from inside VirtualEditor (right-click / ContextMenu
        event on the scroll viewport), not from CustomContextMenu on the
        viewport alone — that path never fired on QAbstractScrollArea.
        """
        enabled = bool(getattr(self._session, "editor_context_menu", True))  # type: ignore[attr-defined]
        editor.set_context_menu_enabled(enabled)
        # Disconnect previous slots to avoid duplicate menus after re-wire
        with suppress(TypeError):
            editor.context_menu_requested.disconnect()
        if enabled:
            editor.context_menu_requested.connect(self._on_editor_context_menu)

    def _on_editor_context_menu(self, global_pos: QPoint) -> None:
        """Slot: global_pos is already in screen coordinates."""
        if not bool(getattr(self._session, "editor_context_menu", True)):  # type: ignore[attr-defined]
            return
        editor = self.sender()
        if not isinstance(editor, VirtualEditor):
            tab = self._current_tab()
            if tab is None or not isinstance(tab.editor, VirtualEditor):
                return
            editor = tab.editor
        self._show_editor_context_menu(editor, global_pos)

    def _spell_word_under_cursor(self, editor: VirtualEditor) -> tuple[str, int, int, int] | None:
        """Return (word, line, start_col, end_col) at caret, or None."""
        tab = self._current_tab()
        if tab is None:
            return None
        lines = read_lines(tab.document)
        hit = word_at(lines, editor._cursor_line, editor._cursor_col)
        if hit is None:
            return None
        word, start, end = hit
        return word, editor._cursor_line, start, end

    def _spell_engine_for_editor(self, editor: VirtualEditor) -> SpellEngine | None:
        eng = getattr(editor, "_spell", None)
        if eng is not None:
            return eng
        # Fall back to primary engine when paint-time spell is off
        return getattr(self, "_spell_engine", None)

    def _apply_spell_suggestion(self, editor: VirtualEditor, suggestion: str) -> None:
        info = self._spell_word_under_cursor(editor)
        if info is None:
            return
        _word, line, start, end = info
        editor.replace_word_on_line(line, start, end, suggestion)

    def _show_editor_context_menu(self, editor: VirtualEditor, global_pos: QPoint) -> None:
        if not bool(getattr(self._session, "editor_context_menu", True)):  # type: ignore[attr-defined]
            return
        clipboard = QApplication.clipboard()
        can_paste = bool(clipboard is not None and clipboard.text())
        undo_stack = getattr(editor, "_undo", []) or []
        redo_stack = getattr(editor, "_redo", []) or []

        # Spell context for word under caret
        spell_word: str | None = None
        spell_misspelled = False
        spell_suggestions: list[str] = []
        eng = self._spell_engine_for_editor(editor)
        session_spell_on = bool(getattr(self._session, "spell_check", True))  # type: ignore[attr-defined]
        if session_spell_on and eng is not None:
            info = self._spell_word_under_cursor(editor)
            if info is not None:
                spell_word, _ln, _a, _b = info
                spell_misspelled = not eng.is_correct(spell_word)
                if spell_misspelled:
                    spell_suggestions = eng.suggest(spell_word, limit=6)

        menu = build_editor_context_menu(
            editor,
            tr=self._tr,  # type: ignore[attr-defined]
            has_selection=editor.has_selection(),
            can_undo=len(undo_stack) > 0,
            can_redo=len(redo_stack) > 0,
            can_paste=can_paste,
            on_undo=editor.undo,
            on_redo=editor.redo,
            on_cut=editor.cut,
            on_copy=editor.copy,
            on_paste=editor.paste,
            on_select_all=editor.select_all,
            on_find=self.show_find,  # type: ignore[attr-defined]
            on_replace=self.show_replace,  # type: ignore[attr-defined]
            on_goto=self.show_goto_line,  # type: ignore[attr-defined]
            on_toggle_comment=self.toggle_comment_current,
            on_indent=self.indent_current,  # type: ignore[attr-defined]
            on_unindent=self.unindent_current,  # type: ignore[attr-defined]
            spell_word=spell_word,
            spell_misspelled=spell_misspelled,
            spell_suggestions=spell_suggestions,
            on_spell_suggestion=(
                (lambda s, ed=editor: self._apply_spell_suggestion(ed, s))
                if spell_misspelled
                else None
            ),
            on_spell_ignore=self.spell_ignore_word if spell_word else None,
            on_spell_add=self.spell_add_word if spell_word else None,
            on_command_palette=self.show_command_palette,
        )
        # global_pos is already screen coordinates from VirtualEditor
        menu.exec(global_pos)

    def _engine_for_langs(self, langs: list[str]) -> SpellEngine:
        key = frozenset(langs) or frozenset({"pt_BR"})
        cache: dict[frozenset[str], SpellEngine] = getattr(self, "_spell_engines", {})
        eng = cache.get(key)
        if eng is None:
            eng = SpellEngine(languages=sorted(key))
            # Share user dict / ignore with primary engine
            base = self._spell_engine
            eng.user_words = base.user_words
            eng.ignore_session = base.ignore_session
            eng.reload_lexicon()
            cache[key] = eng
            self._spell_engines = cache
        return eng

    def _sync_spell_to_editors(self) -> None:
        session = self._session  # type: ignore[attr-defined]
        enabled_global = bool(getattr(session, "spell_check", True))
        for i in range(self.tabs.count()):  # type: ignore[attr-defined]
            w = self.tabs.widget(i)  # type: ignore[attr-defined]
            if w is None or not isinstance(w.editor, VirtualEditor):
                continue
            # Per-tab force, else session force, else auto by syntax language.
            override = getattr(w, "spell_force", None)
            if override is None:
                override = getattr(session, "spell_force", None)
            # When the user toggles spell ON, enable at least for prose + common text;
            # force=True in settings applies to all syntax languages.
            on = enabled_global and spell_enabled_for_language(
                w.language,
                user_override=override,
            )
            if on:
                langs = self._spell_langs_for_tab(w)
                w.editor.set_spell_engine(self._engine_for_langs(langs))
            else:
                w.editor.set_spell_engine(None)

    def toggle_spell_check(self) -> None:
        self._session.spell_check = not bool(getattr(self._session, "spell_check", True))  # type: ignore[attr-defined]
        # When turning on, force spell for current tab so it is visibly active
        if self._session.spell_check:  # type: ignore[attr-defined]
            tab = self._current_tab()
            if tab is not None and tab.spell_force is None:
                # Keep auto for code files; ensure prose/text works
                pass
            # Default session: if spell_force is None, enable for all files so
            # the feature is discoverable (user can still turn off per-tab).
            if getattr(self._session, "spell_force", None) is None:  # type: ignore[attr-defined]
                self._session.spell_force = True  # type: ignore[attr-defined]
        self._sync_spell_to_editors()
        self._update_status_extras()

    def set_tab_spell_languages(self, languages: list[str], tab: EditorTab | None = None) -> None:
        tab = tab or self._current_tab()
        if tab is None:
            return
        cleaned = [x for x in languages if x in SUPPORTED_SPELL_LANGS]
        tab.spell_languages = cleaned or ["pt_BR"]
        tab.spell_force = True  # explicit language choice implies spell on for this file
        session = self._session  # type: ignore[attr-defined]
        session.spell_check = True
        self._sync_spell_to_editors()
        self._update_status_extras()

    def toggle_tab_spell_language(self, lang: str) -> None:
        tab = self._current_tab()
        if tab is None or lang not in SUPPORTED_SPELL_LANGS:
            return
        current = self._spell_langs_for_tab(tab)
        if lang in current:
            if len(current) == 1:
                return  # keep at least one
            current = [x for x in current if x != lang]
        else:
            current = [*current, lang]
        self.set_tab_spell_languages(current, tab)

    def spell_ignore_word(self) -> None:
        tab = self._current_tab()
        if tab is None or not isinstance(tab.editor, VirtualEditor):
            return
        ed = tab.editor
        lines = read_lines(tab.document)
        w = word_at(lines, ed._cursor_line, ed._cursor_col)
        if w:
            self._spell_engine.ignore_word(w[0])
            for eng in getattr(self, "_spell_engines", {}).values():
                eng.ignore_session = self._spell_engine.ignore_session
            ed.viewport().update()

    def spell_add_word(self) -> None:
        tab = self._current_tab()
        if tab is None or not isinstance(tab.editor, VirtualEditor):
            return
        ed = tab.editor
        lines = read_lines(tab.document)
        w = word_at(lines, ed._cursor_line, ed._cursor_col)
        if w:
            self._spell_engine.add_to_user_dict(w[0])
            for eng in getattr(self, "_spell_engines", {}).values():
                eng.user_words = self._spell_engine.user_words
                eng.reload_lexicon()
            ed.viewport().update()

    # --- E / F / H helpers -------------------------------------------

    def show_performance_dashboard(self) -> None:
        tab = self._current_tab()
        session = self._session  # type: ignore[attr-defined]
        if tab is None:
            snap = snapshot_for_document(
                line_count=0,
                buffer_bytes=0,
                huge_mode=False,
                mmap_active=False,
                gpu_acceleration=session.gpu_acceleration,
                portable=is_portable_mode(),
                spell_enabled=bool(getattr(session, "spell_check", True)),
            )
        else:
            doc = tab.document
            snap = snapshot_for_document(
                line_count=doc.line_index().line_count,
                buffer_bytes=len(doc.buffer),
                huge_mode=doc.huge_mode,
                mmap_active=document_mmap_active(doc),
                gpu_acceleration=session.gpu_acceleration,
                portable=is_portable_mode(),
                spell_enabled=bool(getattr(session, "spell_check", True)),
            )
        PerformanceDialog(snap, self).exec()  # type: ignore[arg-type]

    def open_live_preview_browser(self) -> None:
        tab = self._current_tab()
        if tab is None or tab.document.path is None:
            return
        path = tab.document.path
        if path.suffix.lower() in {".html", ".htm", ".md", ".markdown"}:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve())))

    def cancel_long_search(self) -> None:
        self._search_cancel_flag = True
        self._status.set_sync_message(  # type: ignore[attr-defined]
            self._tr.t("search.cancelled", "Search cancelled")  # type: ignore[attr-defined]
        )

    def is_search_cancelled(self) -> bool:
        return self._search_cancel_flag

    def reset_search_cancel(self) -> None:
        self._search_cancel_flag = False

    def _update_status_extras(self) -> None:
        tab = self._current_tab()
        session = self._session  # type: ignore[attr-defined]
        status = self._status  # type: ignore[attr-defined]
        spell_on = bool(getattr(session, "spell_check", True))
        parts = []
        if is_portable_mode():
            parts.append("Portable")
        if tab and tab.document.huge_mode:
            parts.append("mmap")
        if tab and isinstance(tab.editor, VirtualEditor):
            extra = getattr(tab.editor, "_extra_cursors", None) or []
            if extra:
                parts.append(f"{len(extra) + 1} cursors")
            if tab.editor.has_selection():
                sel = tab.editor.selected_text()
                parts.append(f"sel {len(sel)}")
        # Honest MagicCloud: no fake sync
        base = self._tr.t("status.local_only", "Local only")  # type: ignore[attr-defined]
        if parts:
            status.set_sync_message(f"{base} · " + " · ".join(parts))
        else:
            status.set_sync_message(base)
        if tab is not None:
            slang = "+".join(self._spell_langs_for_tab(tab))
        else:
            slang = getattr(session, "spell_language", "") or ""
        if hasattr(status, "set_spell_status"):
            status.set_spell_status(spell_on, slang)

    def export_theme_bundle(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,  # type: ignore[arg-type]
            "Export theme",
            f"{self._session.theme}.json",  # type: ignore[attr-defined]
            "JSON (*.json)",
        )
        if not path:
            return
        data = {
            "theme": self._session.theme,  # type: ignore[attr-defined]
            "icon_pack": getattr(self._session, "icon_pack", "qlementine"),  # type: ignore[attr-defined]
        }
        Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")

    def import_theme_bundle(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import theme", "", "JSON (*.json)")  # type: ignore[arg-type]
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            QMessageBox.warning(self, "Import theme", str(exc))  # type: ignore[arg-type]
            return
        theme = data.get("theme")
        if theme:
            self.apply_theme(str(theme), persist=True)  # type: ignore[attr-defined]


def normalize_paths_equal(a: str, b: str) -> bool:
    try:
        return Path(a).resolve() == Path(b).resolve()
    except OSError:
        return os.path.normcase(a) == os.path.normcase(b)
