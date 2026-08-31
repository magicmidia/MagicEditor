from magiceditor.core.spell_backend import (
    backend_available,
    clear_caches,
    dictionary_path,
    extra_lexicon_path,
    extra_words,
    is_known,
    suggest_words,
)


def test_bundled_pt_dictionary_is_found() -> None:
    from magiceditor.core.spell_hunspell import hunspell_stem

    stem = hunspell_stem()
    assert stem is not None
    assert stem.with_suffix(".dic").is_file()
    assert stem.with_suffix(".aff").is_file()
    assert backend_available("pt_BR")
    path = dictionary_path("pt_BR")
    assert path is not None
    assert path.suffix == ".dic"


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
        "registro",
        "gerenciamento",
        "dirimir",
    ):
        assert is_known(word, langs), word
    assert not is_known("xyzzyqqpt", langs)


def test_brazilian_extra_lexicon_is_loaded() -> None:
    path = extra_lexicon_path("pt_BR")
    assert path is not None and path.is_file()
    extras = extra_words("pt_BR")
    assert "registro" in extras
    assert "gerenciamento" in extras
    assert "dirimir" in extras


def test_pt_br_hunspell_knows_native_brazilian() -> None:
    clear_caches()
    langs = ["pt_BR"]
    for word in (
        "registro",
        "recepção",
        "contato",
        "concepção",
        "aspecto",
        "rastreável",
        "artefato",
        "desbalanceamento",
        "reinjeção",
    ):
        assert is_known(word, langs), word
    assert not is_known("xyzzyqqpt", langs)
    assert not is_known("receção", langs)


def test_pt_br_hunspell_suggests_rastreavel() -> None:
    clear_caches()
    suggestions = [s.casefold() for s in suggest_words("rastrevel", ["pt_BR"], limit=8)]
    assert "rastreável" in suggestions


def test_portuguese_typo_suggests_arquivo() -> None:
    suggestions = [s.casefold() for s in suggest_words("arquvo", ["pt_BR"], limit=8)]
    assert any(s.startswith("arquiv") for s in suggestions)
