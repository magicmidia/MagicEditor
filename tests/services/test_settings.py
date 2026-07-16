"""AppSettings persistence tests."""

from __future__ import annotations

from magiceditor.services.settings import AppSettings, SessionState


def test_settings_roundtrip() -> None:
    s = AppSettings()
    state = SessionState(
        theme="darcula",
        language="pt_BR",
        word_wrap=True,
        line_numbers=False,
        open_files=[],
        active_file=None,
    )
    s.save(state)
    loaded = s.load()
    assert loaded.theme == "darcula"
    assert loaded.language == "pt_BR"
    assert loaded.word_wrap is True
    assert loaded.line_numbers is False
