"""Confirm dialog with stable icon + text layout (avoids broken QMessageBox QSS)."""

from __future__ import annotations

from enum import Enum, auto
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QStyle,
    QVBoxLayout,
    QWidget,
)


class ConfirmResult(Enum):
    SAVE = auto()
    DISCARD = auto()
    CANCEL = auto()
    YES = auto()
    NO = auto()
    OK = auto()


class ConfirmDialog(QDialog):
    """Simple question dialog: icon left, title + body right, buttons bottom.

    Does not use QMessageBox internals, so theme QSS cannot collapse the text
    over the icon.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        title: str = "MagicEditor",
        text: str = "",
        informative: str = "",
        buttons: str = "save_discard_cancel",
        tr: Any | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("confirmDialog")
        self.setModal(True)
        self.setWindowTitle(title)
        self.setMinimumWidth(420)
        self._result = ConfirmResult.CANCEL

        def t(key: str, default: str) -> str:
            if tr is not None and hasattr(tr, "t"):
                return tr.t(key, default)
            return default

        # Icon
        style = self.style()
        icon_label = QLabel(self)
        icon_label.setObjectName("confirmIcon")
        icon_label.setFixedSize(48, 48)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        if style is not None:
            ico: QIcon = style.standardIcon(QStyle.StandardPixmap.SP_MessageBoxQuestion)
            icon_label.setPixmap(ico.pixmap(40, 40))

        # Text column
        text_label = QLabel(text, self)
        text_label.setObjectName("confirmText")
        text_label.setWordWrap(True)
        text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        tf = QFont(text_label.font())
        tf.setPointSize(max(10, tf.pointSize()))
        tf.setBold(True)
        text_label.setFont(tf)
        text_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        info_label = QLabel(informative, self)
        info_label.setObjectName("confirmInfo")
        info_label.setWordWrap(True)
        info_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        info_label.setVisible(bool(informative.strip()))

        text_col = QVBoxLayout()
        text_col.setSpacing(8)
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.addWidget(text_label)
        if informative.strip():
            text_col.addWidget(info_label)
        text_col.addStretch(1)

        body = QHBoxLayout()
        body.setSpacing(16)
        body.setContentsMargins(0, 0, 0, 0)
        body.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignTop)
        body.addLayout(text_col, 1)

        # Buttons
        bbox = QDialogButtonBox(self)
        bbox.setObjectName("confirmButtons")
        if buttons == "save_discard_cancel":
            btn_save = bbox.addButton(
                t("dialog.save", "Salvar"), QDialogButtonBox.ButtonRole.AcceptRole
            )
            btn_discard = bbox.addButton(
                t("dialog.discard", "Descartar"),
                QDialogButtonBox.ButtonRole.DestructiveRole,
            )
            btn_cancel = bbox.addButton(
                t("dialog.cancel", "Cancelar"), QDialogButtonBox.ButtonRole.RejectRole
            )
            btn_save.clicked.connect(lambda: self._finish(ConfirmResult.SAVE))
            btn_discard.clicked.connect(lambda: self._finish(ConfirmResult.DISCARD))
            btn_cancel.clicked.connect(lambda: self._finish(ConfirmResult.CANCEL))
            btn_save.setDefault(True)
            btn_save.setAutoDefault(True)
        elif buttons == "yes_no":
            btn_yes = bbox.addButton(
                t("dialog.yes", "Sim"), QDialogButtonBox.ButtonRole.YesRole
            )
            btn_no = bbox.addButton(
                t("dialog.no", "Não"), QDialogButtonBox.ButtonRole.NoRole
            )
            btn_yes.clicked.connect(lambda: self._finish(ConfirmResult.YES))
            btn_no.clicked.connect(lambda: self._finish(ConfirmResult.NO))
            btn_yes.setDefault(True)
            btn_yes.setAutoDefault(True)
        else:
            btn_ok = bbox.addButton(
                t("dialog.ok", "OK"), QDialogButtonBox.ButtonRole.AcceptRole
            )
            btn_ok.clicked.connect(lambda: self._finish(ConfirmResult.OK))
            btn_ok.setDefault(True)
            btn_ok.setAutoDefault(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 16)
        root.setSpacing(18)
        root.addLayout(body, 1)
        root.addWidget(bbox, 0, Qt.AlignmentFlag.AlignRight)

    def _finish(self, result: ConfirmResult) -> None:
        self._result = result
        if result in (ConfirmResult.CANCEL, ConfirmResult.NO):
            self.reject()
        else:
            self.accept()

    def result_kind(self) -> ConfirmResult:
        return self._result

    @staticmethod
    def ask_save_changes(
        parent: QWidget | None,
        *,
        name: str,
        tr: Any | None = None,
    ) -> ConfirmResult:
        def t(key: str, default: str) -> str:
            if tr is not None and hasattr(tr, "t"):
                return tr.t(key, default)
            return default

        dlg = ConfirmDialog(
            parent,
            title=t("app.name", "MagicEditor"),
            text=t("msg.save_changes", 'Salvar alterações em "{name}"?').format(
                name=name
            ),
            informative=t(
                "msg.save_changes_hint",
                "Se não salvar, as alterações serão perdidas.",
            ),
            buttons="save_discard_cancel",
            tr=tr,
        )
        dlg.exec()
        return dlg.result_kind()

    @staticmethod
    def ask_yes_no(
        parent: QWidget | None,
        *,
        text: str,
        informative: str = "",
        tr: Any | None = None,
    ) -> ConfirmResult:
        def t(key: str, default: str) -> str:
            if tr is not None and hasattr(tr, "t"):
                return tr.t(key, default)
            return default

        dlg = ConfirmDialog(
            parent,
            title=t("app.name", "MagicEditor"),
            text=text,
            informative=informative,
            buttons="yes_no",
            tr=tr,
        )
        dlg.exec()
        return dlg.result_kind()
