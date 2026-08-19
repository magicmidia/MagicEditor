from magiceditor.services.settings_clamp import clamp_int


def test_clamp_int_bounds() -> None:
    assert clamp_int(3, 1, 5, 2) == 3
    assert clamp_int(99, 1, 5, 2) == 5
    assert clamp_int("x", 1, 5, 2) == 2
