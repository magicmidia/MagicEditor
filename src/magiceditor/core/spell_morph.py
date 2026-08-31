"""Conservative Portuguese derivations for spell-check (no Qt).

Accepts a word when a known stem remains after a common prefix/suffix.
Stems shorter than 4 letters are rejected to avoid false positives.
"""

from __future__ import annotations

from collections.abc import Callable

_PREFIXES: tuple[str, ...] = (
    "hiper",
    "super",
    "sobre",
    "entre",
    "contra",
    "trans",
    "inter",
    "extra",
    "ultra",
    "multi",
    "micro",
    "macro",
    "semi",
    "anti",
    "auto",
    "mini",
    "pré",
    "pre",
    "pós",
    "pos",
    "sub",
    "des",
    "re",
    "in",
    "im",
    "co",
)

_SUFFIXES: tuple[str, ...] = (
    "ização",
    "izações",
    "ização",
    "mente",
    "amento",
    "amentos",
    "imento",
    "imentos",
    "áveis",
    "íveis",
    "ável",
    "ível",
    "mento",
    "mentos",
    "agens",
    "agem",
    "idades",
    "idade",
    "ções",
    "ção",
    "osos",
    "osas",
    "oso",
    "osa",
    "antes",
    "entes",
    "ante",
    "ente",
    "adas",
    "ados",
    "ada",
    "ado",
    "ções",
)


def _stem_guesses(stem: str) -> list[str]:
    out = [stem]
    if not stem.endswith(("ar", "er", "ir", "or")):
        out.extend((stem + "ar", stem + "er", stem + "ir", stem + "izar"))
    if stem.endswith("ç"):
        out.append(stem[:-1] + "z")
    return out


def is_known_derivation(word: str, known: Callable[[str], bool]) -> bool:
    """True if *word* is a prefix/suffix of a *known* stem."""
    key = (word or "").casefold().strip()
    if len(key) < 6:
        return False
    for prefix in _PREFIXES:
        if not key.startswith(prefix):
            continue
        rest = key[len(prefix) :]
        if len(rest) < 4:
            continue
        if known(rest):
            return True
        if is_known_derivation(rest, known):
            return True
    for suffix in _SUFFIXES:
        if not key.endswith(suffix):
            continue
        stem = key[: -len(suffix)]
        if len(stem) < 4:
            continue
        for guess in _stem_guesses(stem):
            if known(guess):
                return True
    return False
