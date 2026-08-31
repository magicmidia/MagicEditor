from magiceditor.core.spell_hunspell import available, hunspell_stem, lookup, suggest


def test_vero_files_are_bundled() -> None:
    assert available()
    stem = hunspell_stem()
    assert stem is not None
    assert stem.name == "pt_BR"


def test_vero_lookup_brazilian_words() -> None:
    assert lookup("registro")
    assert lookup("rastreável")
    assert lookup("artefato")
    assert not lookup("xyzzyqqpt")
    assert not lookup("receção")


def test_vero_suggests_typo() -> None:
    hits = [s.casefold() for s in suggest("rastrevel", limit=8)]
    assert "rastreável" in hits
