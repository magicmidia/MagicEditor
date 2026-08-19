import pytest

from magiceditor.core.safe_regex import compile_user_pattern
from magiceditor.core.text_match import PatternError


def test_compile_user_pattern_literal() -> None:
    pat = compile_user_pattern("foo", use_regex=False)
    assert pat.search("xx foo yy")


def test_compile_user_pattern_rejects_long_and_nested() -> None:
    with pytest.raises(PatternError):
        compile_user_pattern("x" * 400, use_regex=True)
    with pytest.raises(PatternError):
        compile_user_pattern("(" * 12 + "a" + ")" * 12, use_regex=True)
