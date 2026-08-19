from magiceditor.ui.virtual_paint import mono_advance


def test_mono_advance_is_char_width_times_cols() -> None:
    assert mono_advance("abcd", 7) == 28
    assert mono_advance("", 10) == 0
    assert mono_advance("x", 0) == 0
