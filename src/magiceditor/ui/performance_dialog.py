"""Performance dashboard dialog."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from magiceditor.services.performance_info import PerformanceSnapshot


class PerformanceDialog(QDialog):
    def __init__(self, snapshot: PerformanceSnapshot, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        title = "Performance"
        if parent is not None:
            tr = getattr(parent, "_tr", None)
            if tr is not None and hasattr(tr, "t"):
                title = tr.t("performance.title", title)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(400, 320)
        body = QLabel("\n".join(snapshot.as_lines()), self)
        body.setTextInteractionFlags(body.textInteractionFlags())  # type: ignore[attr-defined]
        body.setWordWrap(True)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        buttons.clicked.connect(self.accept)
        root = QVBoxLayout(self)
        root.addWidget(body, 1)
        root.addWidget(buttons)
