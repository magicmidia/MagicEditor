"""Find in Files / open tabs — workspace or editor buffers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from magiceditor.core.text_match import PatternError, compile_pattern
from magiceditor.services.folder_search import SearchHit, search_folder, search_texts


class FindInFilesDialog(QDialog):
    """Modal multi-file search."""

    hit_activated = pyqtSignal(str, int, int, str)

    def __init__(
        self,
        root: Path | str | None,
        parent: QWidget | None = None,
        *,
        open_sources: list[tuple[str, str, str]] | None = None,
        tr: Any | None = None,
    ) -> None:
        super().__init__(parent)
        self._root = Path(root) if root else None
        self._open_sources = open_sources or []
        self._tr = tr
        self.setModal(True)
        self.setMinimumSize(560, 400)
        self.setObjectName("findInFilesDialog")

        def t(key: str, default: str) -> str:
            return tr.t(key, default) if tr is not None else default

        self.setWindowTitle(t("find_files.title", "Localizar nos arquivos"))

        self.find_input = QLineEdit(self)
        self.find_input.setPlaceholderText(t("find_files.placeholder", "Pesquisar…"))
        self.case_box = QCheckBox(t("find_files.match_case", "Diferenciar maiúsculas"), self)
        self.regex_box = QCheckBox(t("find_files.regex", "Regex"), self)
        self.scope_box = QComboBox(self)
        self.scope_box.addItem(
            t("find_files.scope_workspace", "Pasta do projeto"), "workspace"
        )
        self.scope_box.addItem(t("find_files.scope_tabs", "Abas abertas"), "tabs")
        if self._root is None or not self._root.is_dir():
            idx = self.scope_box.findData("tabs")
            if idx >= 0:
                self.scope_box.setCurrentIndex(idx)

        self._status = QLabel("", self)
        self._status.setObjectName("findDialogStatus")
        self._results = QListWidget(self)
        self._results.setObjectName("findInFilesResults")
        self._results.itemDoubleClicked.connect(self._open_item)
        self._results.itemActivated.connect(self._open_item)

        btn_search = QPushButton(t("find_files.search", "Pesquisar"), self)
        btn_search.setDefault(True)
        btn_search.clicked.connect(self.run_search)
        btn_close = QPushButton(t("find.close", "Fechar"), self)
        btn_close.clicked.connect(self.reject)

        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(self.find_input, 1)
        row.addWidget(self.scope_box)
        row.addWidget(self.case_box)
        row.addWidget(self.regex_box)
        row.addWidget(btn_search)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(btn_close)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(10)
        root_layout.addLayout(row)
        root_layout.addWidget(self._status)
        root_layout.addWidget(self._results, 1)
        root_layout.addLayout(buttons)

        self.find_input.returnPressed.connect(self.run_search)
        QShortcut(QKeySequence("Esc"), self, activated=self.reject)
        self._update_status_idle()
        self.find_input.setFocus()

    def _t(self, key: str, default: str) -> str:
        if self._tr is not None:
            return self._tr.t(key, default)
        return default

    def _update_status_idle(self) -> None:
        scope = self.scope_box.currentData()
        if scope == "tabs":
            n = len(self._open_sources)
            self._status.setText(
                self._t("find_files.tabs_status", "Abas abertas: {n} buffer(s).").format(n=n)
            )
        elif self._root and self._root.is_dir():
            self._status.setText(
                self._t("find_files.ws_status", "Projeto: {path}").format(path=self._root)
            )
        else:
            self._status.setText(
                self._t(
                    "find_files.no_workspace",
                    "Abra uma pasta (Arquivo → Abrir pasta) para pesquisar.",
                )
            )

    def run_search(self) -> None:
        needle = self.find_input.text()
        if not needle:
            self._status.setText(self._t("find.enter_text", "Digite o texto a localizar."))
            return
        if self.regex_box.isChecked():
            try:
                compile_pattern(
                    needle,
                    case_sensitive=self.case_box.isChecked(),
                    use_regex=True,
                )
            except PatternError as exc:
                self._status.setText(
                    self._t("find.invalid_regex", "Regex inválida: {err}").format(err=exc)
                )
                return

        self._results.clear()
        self._status.setText(self._t("find_files.search", "Pesquisar") + "…")
        scope = self.scope_box.currentData()
        case = self.case_box.isChecked()
        use_re = self.regex_box.isChecked()

        if scope == "tabs":
            if not self._open_sources:
                self._status.setText(
                    self._t("find_files.no_tabs", "Nenhuma aba aberta para pesquisar.")
                )
                return
            hits = search_texts(
                self._open_sources,
                needle,
                case_sensitive=case,
                use_regex=use_re,
            )
        else:
            if self._root is None or not self._root.is_dir():
                self._status.setText(
                    self._t(
                        "find_files.no_workspace",
                        "Abra uma pasta (Arquivo → Abrir pasta) para pesquisar.",
                    )
                )
                return
            hits = search_folder(
                self._root,
                needle,
                case_sensitive=case,
                use_regex=use_re,
            )

        if not hits:
            self._status.setText(self._t("find_files.none", "Nenhuma ocorrência."))
            return

        root_resolved: Path | None = None
        if self._root and self._root.is_dir():
            try:
                root_resolved = self._root.resolve()
            except OSError:
                root_resolved = self._root

        for hit in hits:
            item = QListWidgetItem(self._format_hit(hit, root_resolved))
            item.setData(Qt.ItemDataRole.UserRole, hit)
            self._results.addItem(item)

        key = "find_files.capped" if len(hits) >= 200 else "find_files.hits"
        default = (
            "{n} ocorrência(s) (limite). Clique duas vezes para abrir."
            if len(hits) >= 200
            else "{n} ocorrência(s). Clique duas vezes para abrir."
        )
        self._status.setText(self._t(key, default).format(n=len(hits)))

    def _format_hit(self, hit: SearchHit, root: Path | None) -> str:
        if hit.label:
            path_s = hit.label
        elif root is not None:
            try:
                path_s = hit.path.resolve().relative_to(root).as_posix()
            except (ValueError, OSError):
                path_s = str(hit.path)
        else:
            path_s = str(hit.path)
        return f"{path_s}:{hit.line}:{hit.column}  {hit.text}"

    def _open_item(self, item: QListWidgetItem | None) -> None:
        if item is None:
            return
        hit = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(hit, SearchHit):
            return
        key = hit.source_key or ""
        self.hit_activated.emit(str(hit.path), hit.line, hit.column, key)
