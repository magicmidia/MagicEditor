from magiceditor.core.brace_match import brace_at_or_near, find_matching_brace


def test_find_matching_parens() -> None:
    text = "foo(bar(baz))"
    # position of first (
    assert find_matching_brace(text, 3) == len(text) - 1
    assert find_matching_brace(text, len(text) - 1) == 3


def test_brace_at_or_near() -> None:
    text = "x{y}"
    assert brace_at_or_near(text, 1) == 1
    assert brace_at_or_near(text, 2) == 1  # after { when cursor between
