from magiceditor.core.spell_morph import is_known_derivation


def test_suffix_avel_from_verb() -> None:
    def known(w: str) -> bool:
        return w == "rastrear"

    assert is_known_derivation("rastreável", known)
    assert is_known_derivation("rastreáveis", known)


def test_prefix_plus_known() -> None:
    bag = {"parâmetros", "injeção", "balanceamento"}

    def known(w: str) -> bool:
        return w in bag

    assert is_known_derivation("hiperparâmetros", known)
    assert is_known_derivation("reinjeção", known)
    assert is_known_derivation("desbalanceamento", known)


def test_rejects_short_or_unrelated() -> None:
    def known(w: str) -> bool:
        return w == "casa"

    assert not is_known_derivation("xyz", known)
    assert not is_known_derivation("casinha", known)
