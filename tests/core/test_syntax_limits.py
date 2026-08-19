from magiceditor.core.syntax_limits import SYNTAX_OFF_BYTES, syntax_enabled_for_size


def test_syntax_off_above_20mb() -> None:
    assert syntax_enabled_for_size(SYNTAX_OFF_BYTES) is True
    assert syntax_enabled_for_size(SYNTAX_OFF_BYTES + 1) is False
    assert syntax_enabled_for_size(100, user_enabled=False) is False
