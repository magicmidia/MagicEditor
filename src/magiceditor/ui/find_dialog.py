"""Modal Find / Find & Replace dialogs."""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut, QTextCursor, QTextDocument
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from magiceditor.core.text_match import PatternError, compile_pattern, expand_replacement


def _t(tr: Any | None, key: str, default: str) -> str:
    if tr is not None:
        return tr.t(key, default)
    return default


class FindDialog(QDialog):
    """Centered modal for search (and optional replace)."""

    def __init__(
        self,
        editor: Any,
        parent: QWidget | None = None,
        *,
        replace_mode: bool = False,
        tr: Any | None = None,
    ) -> None:
        super().__init__(parent)
        self._editor = editor
        self._replace_mode = replace_mode
        self._virtual = hasattr(editor, "find_text")
        self._tr = tr
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setObjectName("findDialog")

        t = lambda k, d: _t(tr, k, d)  # noqa: E731

        self.setWindowTitle(
            t("find.replace_title", "Localizar e substituir")
            if replace_mode
            else t("find.title", "Localizar")
        )

        self.find_input = QLineEdit(self)
        self.find_input.setPlaceholderText(t("find.placeholder", "Localizar…"))
        self.replace_input = QLineEdit(self)
        self.replace_input.setPlaceholderText(
            t("find.replace_placeholder", "Substituir por… (\\1 com regex)")
        )
        self.replace_input.setVisible(replace_mode)

        self.case_box = QCheckBox(t("find.match_case", "Diferenciar maiúsculas"), self)
        self.wrap_box = QCheckBox(t("find.wrap", "Circular"), self)
        self.wrap_box.setChecked(True)
        self.regex_box = QCheckBox(t("find.regex", "Expressão regular"), self)

        self._status = QLabel("", self)
        self._status.setObjectName("findDialogStatus")
        if self._virtual and replace_mode:
            self._status.setText(t("find.huge_hint", "Substituir funciona em arquivos grandes."))

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(8)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.addRow(t("find.title", "Localizar") + ":", self.find_input)
        if replace_mode:
            form.addRow(t("find.replace", "Substituir") + ":", self.replace_input)

        options = QHBoxLayout()
        options.setSpacing(12)
        options.addWidget(self.case_box)
        options.addWidget(self.wrap_box)
        options.addWidget(self.regex_box)
        options.addStretch(1)

        self._btn_prev = QPushButton(t("find.prev", "Anterior"), self)
        self._btn_next = QPushButton(t("find.next", "Próximo"), self)
        self._btn_next.setDefault(True)
        self._btn_replace = QPushButton(t("find.replace", "Substituir"), self)
        self._btn_all = QPushButton(t("find.replace_all", "Substituir tudo"), self)
        self._btn_close = QPushButton(t("find.close", "Fechar"), self)

        self._btn_prev.clicked.connect(self.find_prev)
        self._btn_next.clicked.connect(self.find_next)
        self._btn_replace.clicked.connect(self.replace_one)
        self._btn_all.clicked.connect(self.replace_all)
        self._btn_close.clicked.connect(self.reject)

        self._btn_replace.setVisible(replace_mode)
        self._btn_all.setVisible(replace_mode)

        buttons = QHBoxLayout()
        buttons.setSpacing(6)
        buttons.addWidget(self._btn_prev)
        buttons.addWidget(self._btn_next)
        if replace_mode:
            buttons.addWidget(self._btn_replace)
            buttons.addWidget(self._btn_all)
        buttons.addStretch(1)
        buttons.addWidget(self._btn_close)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)
        root.addLayout(form)
        root.addLayout(options)
        root.addWidget(self._status)
        root.addLayout(buttons)

        self.find_input.returnPressed.connect(self.find_next)
        self.find_input.textChanged.connect(self._on_find_text_changed)
        self.case_box.toggled.connect(lambda _c: self._on_find_text_changed(self.find_input.text()))
        self.regex_box.toggled.connect(lambda _c: self._on_find_text_changed(self.find_input.text()))
        QShortcut(QKeySequence("Esc"), self, activated=self.reject)

        if not self._virtual:
            cursor = editor.textCursor()
            if cursor.hasSelection():
                sel = cursor.selectedText().replace("\u2029", "\n")
                if "\n" not in sel:
                    self.find_input.setText(sel)
        self.find_input.selectAll()
        self.find_input.setFocus()
        self._on_find_text_changed(self.find_input.text())

    def _on_find_text_changed(self, text: str) -> None:
        """Incremental find: highlight + in-view / total match count."""
        needle = text or ""
        if self._virtual and hasattr(self._editor, "set_find_highlight"):
            self._editor.set_find_highlight(
                needle,
                case_sensitive=self.case_box.isChecked(),
                use_regex=self.regex_box.isChecked(),
            )
        if not needle:
            self._status.setText("")
            return
        try:
            pattern = compile_pattern(
                needle,
                case_sensitive=self.case_box.isChecked(),
                use_regex=self.regex_box.isChecked(),
            )
        except PatternError as exc:
            self._status.setText(
                self._tt("find.invalid_regex", "Regex inválida: {err}").format(err=exc)
            )
            return
        # Count matches in a bounded sample (viewport-friendly for huge files)
        try:
            if self._virtual and hasattr(self._editor, "document_model"):
                doc = self._editor.document_model()
                sample = doc.text() if len(doc.buffer) <= 2_000_000 else doc.text()[:2_000_000]
            elif hasattr(self._editor, "toPlainText"):
                sample = self._editor.toPlainText()
                if len(sample) > 2_000_000:
                    sample = sample[:2_000_000]
            else:
                sample = ""
            total = len(list(pattern.finditer(sample)))
            self._status.setText(
                self._tt("find.match_count", "{n} ocorrências").format(n=total)
            )
        except Exception:
            pass

    def _tt(self, key: str, default: str) -> str:
        return _t(self._tr, key, default)

    def _flags(self) -> QTextDocument.FindFlag:
        flags = QTextDocument.FindFlag(0)
        if self.case_box.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        if self.regex_box.isChecked():
            flags |= QTextDocument.FindFlag.FindRegularExpression
        return flags

    def _validate_pattern(self) -> bool:
        needle = self.find_input.text()
        if not needle:
            self._status.setText(self._tt("find.enter_text", "Digite o texto a localizar."))
            return False
        if not self.regex_box.isChecked():
            return True
        try:
            compile_pattern(
                needle,
                case_sensitive=self.case_box.isChecked(),
                use_regex=True,
            )
        except PatternError as exc:
            self._status.setText(
                self._tt("find.invalid_regex", "Regex inválida: {err}").format(err=exc)
            )
            return False
        return True

    def find_next(self) -> None:
        self._find(backward=False)

    def find_prev(self) -> None:
        self._find(backward=True)

    def _find(self, *, backward: bool) -> None:
        if not self._validate_pattern():
            return
        text = self.find_input.text()

        if self._virtual:
            found = self._editor.find_text(
                text,
                case_sensitive=self.case_box.isChecked(),
                backward=backward,
                wrap=self.wrap_box.isChecked(),
                use_regex=self.regex_box.isChecked(),
            )
            if found:
                self._status.setText(self._tt("find.found", "Ocorrência encontrada."))
                self._editor.centerCursor()
            else:
                self._status.setText(self._tt("find.none", "Nenhuma ocorrência."))
            return

        flags = self._flags()
        if backward:
            flags |= QTextDocument.FindFlag.FindBackward
        found = self._editor.find(text, flags)
        if not found and self.wrap_box.isChecked():
            cursor = self._editor.textCursor()
            cursor.movePosition(
                QTextCursor.MoveOperation.End if backward else QTextCursor.MoveOperation.Start
            )
            self._editor.setTextCursor(cursor)
            found = self._editor.find(text, flags)
        if found:
            self._status.setText(self._tt("find.found", "Ocorrência encontrada."))
            self._editor.centerCursor()
        else:
            self._status.setText(self._tt("find.none", "Nenhuma ocorrência."))

    def replace_one(self) -> None:
        if not self._replace_mode or not self._validate_pattern():
            return
        needle = self.find_input.text()
        repl = self.replace_input.text()

        if self._virtual and hasattr(self._editor, "replace_text"):
            ok = self._editor.replace_text(
                needle,
                repl,
                case_sensitive=self.case_box.isChecked(),
                use_regex=self.regex_box.isChecked(),
            )
            self._status.setText(
                self._tt("find.replaced_one", "1 ocorrência substituída.")
                if ok
                else self._tt("find.none", "Nenhuma ocorrência.")
            )
            return

        cursor = self._editor.textCursor()
        if cursor.hasSelection() and self._selection_matches(cursor, needle):
            selected = cursor.selectedText().replace("\u2029", "\n")
            if self.regex_box.isChecked():
                try:
                    pat = compile_pattern(
                        needle,
                        case_sensitive=self.case_box.isChecked(),
                        use_regex=True,
                    )
                    m = pat.fullmatch(selected) or pat.match(selected)
                    text = expand_replacement(m, repl) if m else repl
                except PatternError:
                    text = repl
            else:
                text = repl
            cursor.insertText(text)
            self._status.setText(self._tt("find.replaced_one", "1 ocorrência substituída."))
        self.find_next()

    def replace_all(self) -> None:
        if not self._replace_mode or not self._validate_pattern():
            return
        needle = self.find_input.text()
        repl = self.replace_input.text()

        if self._virtual and hasattr(self._editor, "replace_all_text"):
            count = self._editor.replace_all_text(
                needle,
                repl,
                case_sensitive=self.case_box.isChecked(),
                use_regex=self.regex_box.isChecked(),
            )
            key = "find.replaced_capped" if count >= 50_000 else "find.replaced_n"
            default = (
                "{n} ocorrência(s) substituída(s) (limite)."
                if count >= 50_000
                else "{n} ocorrência(s) substituída(s)."
            )
            self._status.setText(self._tt(key, default).format(n=count))
            return

        if self.regex_box.isChecked():
            try:
                pat = compile_pattern(
                    needle,
                    case_sensitive=self.case_box.isChecked(),
                    use_regex=True,
                )
            except PatternError as exc:
                self._status.setText(
                    self._tt("find.invalid_regex", "Regex inválida: {err}").format(err=exc)
                )
                return
            plain = self._editor.toPlainText()
            new_text, count = pat.subn(repl, plain)
            if count:
                cursor = self._editor.textCursor()
                cursor.beginEditBlock()
                cursor.select(QTextCursor.SelectionType.Document)
                cursor.insertText(new_text)
                cursor.endEditBlock()
            self._status.setText(
                self._tt("find.replaced_n", "{n} ocorrência(s) substituída(s).").format(n=count)
            )
            return

        doc = self._editor.document()
        cursor = QTextCursor(doc)
        cursor.beginEditBlock()
        count = 0
        flags = self._flags()
        while True:
            cursor = doc.find(needle, cursor, flags)
            if cursor.isNull():
                break
            cursor.insertText(repl)
            count += 1
        cursor.endEditBlock()
        self._status.setText(
            self._tt("find.replaced_n", "{n} ocorrência(s) substituída(s).").format(n=count)
        )

    def _selection_matches(self, cursor: QTextCursor, needle: str) -> bool:
        selected = cursor.selectedText().replace("\u2029", "\n")
        if self.regex_box.isChecked():
            try:
                pat = compile_pattern(
                    needle,
                    case_sensitive=self.case_box.isChecked(),
                    use_regex=True,
                )
            except PatternError:
                return False
            return pat.fullmatch(selected) is not None or pat.match(selected) is not None
        if self.case_box.isChecked():
            return selected == needle
        return selected.lower() == needle.lower()
