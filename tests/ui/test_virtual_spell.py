from magiceditor.ui.syntax_cache import LineTokenCache
from magiceditor.ui.virtual_spell import spans_from_engine


class _Hit:
    def __init__(self, start: int, end: int) -> None:
        self.start = start
        self.end = end


class _Engine:
    def check_text(self, text: str):
        if "teh" in text:
            i = text.index("teh")
            return [_Hit(i, i + 3)]
        return []


def test_spell_spans_from_engine() -> None:
    assert spans_from_engine(_Engine(), "teh cat") == ((0, 3),)
    assert spans_from_engine(None, "teh") == ()


def test_line_token_cache_reuses_same_line() -> None:
    cache = LineTokenCache()
    a = cache.tokens(0, "def x():", "python")
    b = cache.tokens(0, "def x():", "python")
    assert a is b
    cache.invalidate()
    c = cache.tokens(0, "def x():", "python")
    assert c is not a


def test_line_token_cache_recomputes_when_text_changes() -> None:
    cache = LineTokenCache()
    a = cache.tokens(0, "def x():", "python")
    b = cache.tokens(0, "def y():", "python")
    assert a is not b
