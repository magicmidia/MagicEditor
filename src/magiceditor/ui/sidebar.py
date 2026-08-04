"""Workspace sidebar — mockup Luminous Void layout (nav + open editors + tree)."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFileSystemModel, QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from magiceditor.version import version_label


class _NavButton(QPushButton):
    """Full-width sidebar nav row (Explorer / Search / Settings)."""

    def __init__(self, label: str, parent: QWidget | None = None) -> None:
        super().__init__(label, parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("sidebarNavButton")
        self.setFlat(True)
        self.setMinimumHeight(32)


class Sidebar(QWidget):
    """Project sidebar matching the mockup structure.

    Signals:
        file_activated — path of a file to open
        search_requested — open Find in Files / quick search
        settings_requested — open Settings
    """

    file_activated = pyqtSignal(str)
    search_requested = pyqtSignal()
    settings_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("workspaceSidebar")
        self.setMinimumWidth(220)
        self.setMaximumWidth(360)

        # --- Header (Workspace) ---
        self._ws_title = QLabel("Workspace", self)
        self._ws_title.setObjectName("sidebarWorkspaceTitle")
        self._ws_sub = QLabel(version_label(), self)
        self._ws_sub.setObjectName("sidebarWorkspaceSub")
        badge = QLabel("✦", self)
        badge.setObjectName("sidebarWorkspaceBadge")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedSize(24, 24)

        header_text = QVBoxLayout()
        header_text.setSpacing(0)
        header_text.setContentsMargins(0, 0, 0, 0)
        header_text.addWidget(self._ws_title)
        header_text.addWidget(self._ws_sub)

        header = QHBoxLayout()
        header.setContentsMargins(12, 10, 12, 10)
        header.setSpacing(8)
        header.addWidget(badge)
        header.addLayout(header_text, 1)

        header_frame = QFrame(self)
        header_frame.setObjectName("sidebarHeader")
        header_frame.setLayout(header)

        # --- Nav ---
        self._btn_explorer = _NavButton("  Explorer", self)
        self._btn_search = _NavButton("  Search", self)
        self._btn_settings = _NavButton("  Settings", self)
        self._btn_explorer.setChecked(True)
        self._btn_explorer.setProperty("activeNav", True)
        self._btn_search.clicked.connect(self.search_requested.emit)
        self._btn_settings.clicked.connect(self.settings_requested.emit)
        # Explorer keeps panel visible; re-check
        self._btn_explorer.clicked.connect(lambda: self._set_nav("explorer"))

        nav = QVBoxLayout()
        nav.setContentsMargins(6, 6, 6, 6)
        nav.setSpacing(2)
        nav.addWidget(self._btn_explorer)
        nav.addWidget(self._btn_search)
        nav.addWidget(self._btn_settings)
        nav.addStretch(1)

        nav_frame = QFrame(self)
        nav_frame.setObjectName("sidebarNav")
        nav_frame.setLayout(nav)
        nav_frame.setFixedHeight(130)

        # --- Open Editors ---
        self._open_label = QLabel("OPEN EDITORS", self)
        self._open_label.setObjectName("sidebarSectionLabel")
        self._open_list = QListWidget(self)
        self._open_list.setObjectName("sidebarOpenEditors")
        self._open_list.setMaximumHeight(100)
        self._open_list.setSpacing(1)
        self._open_list.itemClicked.connect(self._on_open_item)

        # --- Project tree ---
        self._proj_label = QLabel("PROJECT FILES", self)
        self._proj_label.setObjectName("sidebarSectionLabel")
        self._tree = QTreeView(self)
        self._tree.setObjectName("sidebarTree")
        self._model = QFileSystemModel(self)
        self._model.setRootPath("")
        self._tree.setModel(self._model)
        self._tree.setRootIndex(self._model.index(str(Path.home())))
        for col in range(1, 4):
            self._tree.hideColumn(col)
        self._tree.setHeaderHidden(True)
        self._tree.setAnimated(True)
        self._tree.setIndentation(14)
        self._tree.doubleClicked.connect(self._on_double_clicked)
        self._tree.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        body = QVBoxLayout()
        body.setContentsMargins(8, 4, 8, 8)
        body.setSpacing(4)
        body.addWidget(self._open_label)
        body.addWidget(self._open_list)
        body.addWidget(self._proj_label)
        body.addWidget(self._tree, 1)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(header_frame)
        root.addWidget(nav_frame)
        root.addLayout(body, 1)

        mono = QFont("Cascadia Code")
        mono.setPointSize(9)
        self._open_list.setFont(mono)
        self._tree.setFont(mono)

    def set_root_path(self, path: str | Path) -> None:
        path = str(path)
        self._model.setRootPath(path)
        self._tree.setRootIndex(self._model.index(path))
        name = Path(path).name or path
        self._ws_title.setText(name)

    def set_workspace_label(self, name: str) -> None:
        self._ws_title.setText(name or self._ws_title.text())

    def retranslate(self, tr) -> None:
        """Apply UI language to fixed labels."""
        t = tr.t
        if self._ws_title.text() in {"Workspace", "Área de trabalho", ""}:
            self._ws_title.setText(t("panel.workspace", "Área de trabalho"))
        self._btn_explorer.setText("  " + t("nav.explorer", "Explorador"))
        self._btn_search.setText("  " + t("nav.search", "Pesquisar"))
        self._btn_settings.setText("  " + t("nav.settings", "Configurações"))
        self._open_label.setText(t("panel.open_editors", "Editores abertos").upper())
        self._proj_label.setText(t("panel.project_files", "Arquivos do projeto").upper())

    def set_open_editors(self, items: list[tuple[str, str]]) -> None:
        """``items``: list of (display_name, path_or_key)."""
        self._open_list.clear()
        for label, key in items:
            item = QListWidgetItem(f"  {label}")
            item.setData(Qt.ItemDataRole.UserRole, key)
            self._open_list.addItem(item)

    def _set_nav(self, which: str) -> None:
        self._btn_explorer.setChecked(which == "explorer")
        self._btn_search.setChecked(which == "search")
        self._btn_settings.setChecked(which == "settings")

    def _on_double_clicked(self, index) -> None:
        path = self._model.filePath(index)
        if path and not self._model.isDir(index):
            self.file_activated.emit(path)

    def _on_open_item(self, item: QListWidgetItem) -> None:
        key = item.data(Qt.ItemDataRole.UserRole)
        if key:
            self.file_activated.emit(str(key))
