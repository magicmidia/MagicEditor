"""J2 layer Aceites: no ui read_bytes, viewport-only editor, viewport_text."""

from __future__ import annotations

from pathlib import Path

import pytest

import magiceditor.ui as ui_pkg
from magiceditor.core.document import Document
from magiceditor.core.editor_surface import EditorSurface
from magiceditor.core.piece_table import PieceTable
from magiceditor.services.document_io import open_document


def test_ui_package_has_no_read_bytes() -> None:
    """J2.1: size/mmap policy stays in document_io; ui/ never calls read_bytes."""
    root = Path(ui_pkg.__file__).resolve().parent
    offenders: list[str] = []
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "read_bytes" in text:
            offenders.append(str(path.relative_to(root)))
    assert offenders == []


def test_open_document_is_huge_gate(tmp_path: Path) -> None:
    """J2.1: open_document sets huge_mode from file size."""
    small = tmp_path / "small.txt"
    small.write_text("ok\n", encoding="utf-8")
    assert open_document(small).huge_mode is False
    big = tmp_path / "big.txt"
    big.write_bytes(b"x" * (5 * 1024 * 1024 + 64))
    assert open_document(big).huge_mode is True


def test_document_io_no_longer_documents_classic_editor() -> None:
    """J2.2: open_document docstring must not advertise a classic editor path."""
    assert "classic editor" not in (open_document.__doc__ or "").lower()


def test_main_window_has_no_text_editor_branch() -> None:
    """J2.2: MainWindow no longer imports or branches on TextEditor."""
    src = Path(ui_pkg.__file__).resolve().parent / "main_window.py"
    text = src.read_text(encoding="utf-8")
    assert "TextEditor" not in text
    assert "from magiceditor.ui.text_editor" not in text


def test_text_editor_shim_refuses_construct() -> None:
    """J2.2 / M6: leftover import must not revive QPlainTextEdit."""
    from magiceditor.ui.text_editor import TextEditor

    with pytest.raises(RuntimeError, match="VirtualEditor"):
        TextEditor()


@pytest.mark.ui
def test_editor_tab_is_always_virtual(qtbot) -> None:
    """J2.2: EditorTab hosts VirtualEditor only (no classic branch)."""
    pytest.importorskip("PyQt6")
    pytest.importorskip("pytestqt")
    from magiceditor.ui.editor_tab import EditorTab
    from magiceditor.ui.virtual_editor import VirtualEditor

    tab = EditorTab(Document.from_text("hello\nworld"))
    qtbot.addWidget(tab)
    assert type(tab.editor) is VirtualEditor
    assert isinstance(tab.editor, EditorSurface)


@pytest.mark.ui
def test_viewport_text_is_visible_range_not_full_buffer(qtbot) -> None:
    """J2.3: viewport_text() returns visible lines; full_text stays fail-closed."""
    pytest.importorskip("PyQt6")
    pytest.importorskip("pytestqt")
    from magiceditor.ui.editor_tab import EditorTab
    from magiceditor.ui.virtual_editor import VirtualEditor

    body = "\n".join(f"LINE-{i:03d}" for i in range(80))
    doc = Document.from_text(body)
    ed = VirtualEditor(doc)
    qtbot.addWidget(ed)
    ed.resize(480, 72)
    visible = ed.viewport_text()
    assert "LINE-000" in visible
    assert "LINE-079" not in visible

    tab = EditorTab(Document.from_text(body))
    qtbot.addWidget(tab)
    tab.editor.resize(480, 72)
    assert tab.viewport_text() == tab.editor.viewport_text()
    assert "LINE-000" in tab.export_text()

    huge = Document(buffer=PieceTable("secret-payload"), huge_mode=True)
    with pytest.raises(ValueError, match="max_bytes"):
        huge.full_text(max_bytes=None)
    assert "secret" in huge.full_text(max_bytes=64)


def test_tab_manager_source_has_no_hardcoded_pt_menu() -> None:
    """J2.4: tab context menu is not baked-in Portuguese."""
    src = (Path(ui_pkg.__file__).resolve().parent / "tab_manager.py").read_text(encoding="utf-8")
    assert 'addAction("Fechar aba")' not in src
    assert 'addAction("Novo grupo com esta aba")' not in src
    assert 'setToolTip("Novo arquivo")' not in src


@pytest.mark.ui
def test_status_bar_local_only_from_locale(qtbot) -> None:
    """J2.4: status_bar Local-only / spell copy comes from locales."""
    pytest.importorskip("PyQt6")
    pytest.importorskip("pytestqt")
    from magiceditor.i18n.translator import TranslatorManager
    from magiceditor.ui.status_bar import EditorStatusBar

    tr = TranslatorManager()
    tr.load("pt_BR")
    bar = EditorStatusBar()
    qtbot.addWidget(bar)
    bar.set_translator(tr)
    assert bar._sync.text() == "Só local"
    bar.set_spell_status(False)
    assert "Ortografia" in bar._spell.text()
