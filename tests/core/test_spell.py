from magiceditor.core.spell import (
    SpellEngine,
    iter_words,
    spell_enabled_for_language,
)


def test_spell_default_languages() -> None:
    assert spell_enabled_for_language("markdown") is True
    assert spell_enabled_for_language("python") is False
    assert spell_enabled_for_language("python", user_override=True) is True


def test_spell_engine_marks_unknown() -> None:
    eng = SpellEngine(language="en_US")
    hits = eng.check_text("hello xyzzyqq world")
    words = {h.word for h in hits}
    assert "xyzzyqq" in words
    assert "hello" not in words


def test_user_dict_and_ignore() -> None:
    eng = SpellEngine(language="en_US")
    eng.add_to_user_dict("xyzzyqq")
    assert eng.check_text("xyzzyqq") == []
    eng2 = SpellEngine(language="en_US")
    eng2.ignore_word("blorb")
    assert eng2.check_text("blorb") == []


def test_iter_words() -> None:
    words = iter_words("Hello, world!")
    assert [w for _, _, w in words] == ["Hello", "world"]


def test_multi_language_union() -> None:
    eng = SpellEngine(languages=["pt_BR", "en_US"])
    hits = eng.check_text("hello mundo xyzzyqq")
    words = {h.word for h in hits}
    assert "hello" not in words
    assert "mundo" not in words
    assert "xyzzyqq" in words


def test_set_languages() -> None:
    eng = SpellEngine(language="en_US")
    eng.set_languages(["es_ES", "pt_BR"])
    assert set(eng.active_languages()) == {"es_ES", "pt_BR"}


def test_suggest_returns_close_words() -> None:
    eng = SpellEngine(language="en_US")
    # "helo" is close to "hello" in the embedded en_US lexicon
    suggestions = eng.suggest("helo", limit=5)
    assert any(s.casefold() == "hello" for s in suggestions)


def test_suggest_empty_when_correct() -> None:
    eng = SpellEngine(language="en_US")
    assert eng.suggest("hello") == []
