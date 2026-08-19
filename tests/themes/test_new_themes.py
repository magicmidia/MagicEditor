from pathlib import Path

from magiceditor.themes.manager import NATIVE_THEMES, ThemeManager
from magiceditor.themes.tokens import chrome_tokens


def test_new_editor_themes_are_registered() -> None:
    added = ("tokyo_night", "catppuccin_mocha", "nord", "rose_pine")
    for tid in added:
        assert tid in NATIVE_THEMES


def test_new_theme_qss_files_exist_and_load() -> None:
    mgr = ThemeManager()
    for tid in ("tokyo_night", "catppuccin_mocha", "nord", "rose_pine"):
        qss = mgr.load_qss(tid)
        assert "QMainWindow" in qss
        assert "QDialog QLabel" in qss
        assert chrome_tokens(tid).accent.lower() in qss.lower()
        path = Path("resources/themes") / f"{tid}.qss"
        assert path.is_file()


def test_new_theme_tokens_are_distinct() -> None:
    accents = {
        chrome_tokens(tid).accent.lower()
        for tid in ("tokyo_night", "catppuccin_mocha", "nord", "rose_pine")
    }
    assert len(accents) == 4
    backgrounds = {
        chrome_tokens(tid).bg.lower()
        for tid in ("tokyo_night", "catppuccin_mocha", "nord", "rose_pine")
    }
    assert len(backgrounds) == 4
