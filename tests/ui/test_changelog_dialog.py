"""Help → Novidades renders the bundled changelog."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("PyQt6")
pytest.importorskip("pytestqt")

from magiceditor.ui.changelog_dialog import ChangelogDialog
from magiceditor.version import VERSION

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.ui
def test_changelog_dialog_shows_current_version(qtbot) -> None:
    dialog = ChangelogDialog()
    qtbot.addWidget(dialog)
    plain = dialog.view.toPlainText()
    assert VERSION in plain
    assert "Novidades" in dialog.windowTitle()


@pytest.mark.ui
def test_changelog_dialog_missing_file(qtbot, monkeypatch) -> None:
    monkeypatch.setattr("magiceditor.ui.changelog_dialog.read_changelog", lambda: "")
    dialog = ChangelogDialog()
    qtbot.addWidget(dialog)
    assert "não foi encontrado" in dialog.view.toPlainText()


def test_changelog_strings_in_every_locale() -> None:
    keys = {"action.changelog", "msg.changelog_title", "msg.changelog_missing"}
    for name in ("pt_BR.json", "en_US.json", "es_ES.json"):
        data = json.loads((ROOT / "locales" / name).read_text(encoding="utf-8"))
        missing = keys - data.keys()
        assert not missing, f"{name} missing {missing}"
