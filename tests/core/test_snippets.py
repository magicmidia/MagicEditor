from magiceditor.core.snippets import expand_snippet, match_trigger


def test_expand_snippet_cursor() -> None:
    text, cur = expand_snippet("hello $0 world")
    assert "hello" in text and "world" in text
    assert "$0" not in text
    assert 0 <= cur <= len(text)


def test_match_trigger_python() -> None:
    sn = match_trigger("def", "python")
    assert sn is not None
    assert sn.trigger == "def"
