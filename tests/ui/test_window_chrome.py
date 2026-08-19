"""J1.2: menus/actions live in window_chrome, not MainWindow."""

from magiceditor.ui.window_chrome import ACTION_ICON_MAP, ACTION_SPECS, action_ids
from magiceditor.ui.window_files import apply_save_prefs


def test_action_specs_cover_core_commands() -> None:
    keys = set(action_ids())
    for needed in (
        "action.new",
        "action.save",
        "action.command_palette",
        "action.preview",
        "action.toggle_spell",
        "action.exit",
    ):
        assert needed in keys
    assert all(len(spec) == 4 for spec in ACTION_SPECS)
    assert ACTION_ICON_MAP["action.save"] == "save"
    assert "action.new" in ACTION_ICON_MAP


def test_apply_save_prefs_trim_and_newline() -> None:
    assert apply_save_prefs("ab  \ncd  ", trim=True, final_nl=True) == "ab\ncd\n"
    assert apply_save_prefs("ok", trim=False, final_nl=True) == "ok\n"
    assert apply_save_prefs("ok\n", trim=False, final_nl=False) == "ok\n"
