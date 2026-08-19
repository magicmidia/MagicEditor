"""Settings dialog shell — pages live in settings_pages/ (J1.4)."""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import QSize
from PyQt6.QtGui import QFont, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from magiceditor.services.settings import SessionState
from magiceditor.ui.settings_pages.design import DesignPage
from magiceditor.ui.settings_pages.editor import EditorPage
from magiceditor.ui.settings_pages.general import PAGE_ID as GENERAL_PAGE_ID
from magiceditor.ui.settings_pages.general import GeneralPage
from magiceditor.ui.settings_pages.graphics import GraphicsPage
from magiceditor.ui.settings_pages.performance import PerformancePage
from magiceditor.ui.settings_pages.spell import SpellPage
from magiceditor.ui.settings_pages.tabs import TabsPage


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
        self.setMinimumSize(780, 580)
        self.resize(860, 660)
        self.setObjectName("settingsDialog")

        def t(key: str, default: str) -> str:
            if self._tr is not None:
                return self._tr.t(key, default)
            return default

        self._t = t
        self.setWindowTitle(t("settings.title", "Configurações"))

        langs = languages or ["pt_BR", "en_US", "es_ES"]
        self._general = GeneralPage(state, t, langs)
        self._editor = EditorPage(state, t)
        self._spell = SpellPage(state, t)
        self._design = DesignPage(state, t)
        self._graphics = GraphicsPage(state, t)
        self._tabs = TabsPage(state, t)
        self._performance = PerformancePage(state, t)
        self._pages = (
            self._general,
            self._editor,
            self._spell,
            self._design,
            self._graphics,
            self._tabs,
            self._performance,
        )
        self._alias_page_widgets()

        self.nav = QListWidget(self)
        self.nav.setObjectName("settingsNav")
        self.nav.setFixedWidth(220)
        self.nav.setSpacing(4)
        self.nav.setUniformItemSizes(True)
        nav_font = QFont(self.nav.font())
        nav_font.setPointSize(max(10, nav_font.pointSize() + 1))
        nav_font.setBold(True)
        self.nav.setFont(nav_font)
        subjects = [
            (GENERAL_PAGE_ID, t("settings.tab.general", "Geral")),
            ("editor", t("settings.tab.editor", "Editor")),
            ("spell", t("settings.tab.spell", "Ortografia")),
            ("design", t("settings.tab.design", "Design")),
            ("graphics", t("settings.tab.graphics", "Gráficos")),
            ("tabs", t("settings.tab.tabs", "Abas")),
            ("performance", t("settings.tab.performance", "Desempenho")),
        ]
        for _sid, label in subjects:
            item = QListWidgetItem(label)
            item.setSizeHint(QSize(200, 48))
            self.nav.addItem(item)

        self.stack = QStackedWidget(self)
        for page in self._pages:
            self.stack.addWidget(page)
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

    def _alias_page_widgets(self) -> None:
        """Expose page controls on the dialog (existing tests + apply callers)."""
        for page in self._pages:
            for name, value in vars(page).items():
                if name.startswith("_"):
                    continue
                setattr(self, name, value)

    def apply_to_state(self, state: SessionState) -> SessionState:
        """Mutate and return ``state`` with dialog values."""
        for page in self._pages:
            page.apply(state)
        return state
