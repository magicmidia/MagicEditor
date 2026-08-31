from pathlib import Path

from magiceditor.themes.manager import NATIVE_THEMES, ThemeManager, _chrome_extras
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


def test_chrome_extras_checkbox_and_compact_menu() -> None:
    qss = _chrome_extras("luminous_void")
    assert "QMenu {" in qss
    assert "min-width" not in qss
    assert "min-height: 26px" not in qss
    assert "QMenu::item" in qss
    assert "padding: 3px 28px 3px 24px" in qss
    assert "check.svg" in qss
    light = _chrome_extras("clean_light")
    assert "check_dark.svg" in light
