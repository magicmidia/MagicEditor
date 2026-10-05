"""Help menu changelog. Renders the bundled Keep a Changelog file."""

from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import QDialog, QPushButton, QTextBrowser, QVBoxLayout, QWidget

from magiceditor.paths import read_changelog
from magiceditor.preview.markdown_preview import render_markdown
from magiceditor.version import version_display

_CSS = (
    "body { font-size: 14px; }"
    "h1 { font-size: 20px; }"
    "h2 { font-size: 16px; margin-top: 1.1em; }"
    "code, pre { font-family: Cascadia Code, Consolas, monospace; }"
    "a { color: #2563eb; }"
)


class ChangelogDialog(QDialog):
    """Read-only view of ``docs/CHANGELOG.md``."""

    def __init__(self, parent: QWidget | None = None, *, tr: Any | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("changelogDialog")
        self.setModal(True)
        self.setMinimumSize(640, 520)

        def t(key: str, default: str) -> str:
            return tr.t(key, default) if tr is not None else default

        self.setWindowTitle(t("msg.changelog_title", "Novidades"))
        layout = QVBoxLayout(self)
        self.view = QTextBrowser(self)
        self.view.setObjectName("changelogView")
        self.view.setOpenExternalLinks(True)
        self.view.document().setDefaultStyleSheet(_CSS)
        text = read_changelog()
        if text.strip():
            self.view.setHtml(render_markdown(text))
        else:
            self.view.setPlainText(
                t(
                    "msg.changelog_missing",
                    "O registro de alterações não foi encontrado nesta instalação.",
                )
            )
        layout.addWidget(self.view, stretch=1)
        close = QPushButton(t("dialog.close", "Fechar"), self)
        close.clicked.connect(self.accept)
        layout.addWidget(close)


def show_changelog(window: Any) -> None:
    """Open the changelog for the running window."""
    tr = getattr(window, "_tr", None)
    dialog = ChangelogDialog(window, tr=tr)
    dialog.setWindowTitle(dialog.windowTitle() + f" — {version_display()}")
    dialog.exec()
