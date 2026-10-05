"""Auto-close bracket decisions (no Qt)."""

from magiceditor.ui.bracket_edit import bracket_insert


def test_pair_and_wrap() -> None:
    assert bracket_insert("(", "", "") == ("()", 1)
    assert bracket_insert("(", "ab", "") == ("(ab)", 1)
    assert bracket_insert("[", "", "") == ("[]", 1)
    assert bracket_insert("{", "", "x") == ("{}", 1)


def test_skip_closer_and_quote() -> None:
    assert bracket_insert(")", "", ")") == ("", -1)
    assert bracket_insert(")", "", "x") is None
    assert bracket_insert('"', "", "") == ('""', 1)
    assert bracket_insert('"', "", '"') == ("", -1)
    assert bracket_insert("'", "z", "'") == ("'z'", 1)


def test_plain_character_ignored() -> None:
    assert bracket_insert("a", "", "") is None
    assert bracket_insert("ab", "", "") is None
