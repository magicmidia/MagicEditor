from magiceditor.core.spell_backend import (
    backend_available,
    dictionary_path,
    is_known,
    suggest_words,
)


def test_bundled_pt_dictionary_is_found() -> None:
    path = dictionary_path("pt_BR")
    assert path is not None
    assert path.is_file()
    assert backend_available("pt_BR")


def test_common_portuguese_words_are_known() -> None:
    langs = ["pt_BR"]
    for word in (
        "casa",
        "amanhã",
        "configurações",
        "arquivo",
        "obrigado",
        "também",
        "porque",
        "trabalho",
        "pessoa",
    ):
        assert is_known(word, langs), word
    assert not is_known("xyzzyqqpt", langs)


def test_portuguese_typo_suggests_arquivo() -> None:
    suggestions = [s.casefold() for s in suggest_words("arquvo", ["pt_BR"], limit=8)]
    assert any(s.startswith("arquiv") for s in suggestions)
