"""Spell dictionaries behind SpellEngine.

``pt_BR`` uses the native LibreOffice VERO Hunspell (``.dic``/``.aff``).
``en_US`` / ``es_ES`` use bundled pyspellchecker frequency lists.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Product codes → dictionary file stem (pyspellchecker)
_CODES: dict[str, str] = {
    "pt_BR": "pt",
    "en_US": "en",
    "es_ES": "es",
}

_cache: dict[str, Any] = {}
_extra_cache: dict[str, frozenset[str]] = {}


def dictionary_candidates(lang: str) -> list[Path]:
    """Search paths for the language's primary dictionary file."""
    out: list[Path] = []
    try:
        from magiceditor.paths import resource_root

        root = resource_root()
        if lang == "pt_BR":
            out.append(root / "resources" / "spell" / "pt_BR.dic")
        code = _CODES.get(lang)
        if code:
            out.append(root / "resources" / "spell" / f"{code}.json.gz")
            out.append(root / "spellchecker" / "resources" / f"{code}.json.gz")
    except Exception:
        pass
    try:
        import spellchecker as sc

        pkg = Path(sc.__file__).resolve().parent
        code = _CODES.get(lang)
        if code:
            out.append(pkg / "resources" / f"{code}.json.gz")
    except Exception:
        pass
    return out


def extra_lexicon_path(lang: str) -> Path | None:
    """Bundled extra word list (``resources/spell/pt_BR.txt``)."""
    try:
        from magiceditor.paths import resource_root

        path = resource_root() / "resources" / "spell" / f"{lang}.txt"
    except Exception:
        return None
    return path if path.is_file() else None


def clear_caches() -> None:
    _cache.clear()
    _extra_cache.clear()


def extra_words(lang: str) -> frozenset[str]:
    """Optional extra word list (``resources/spell/{lang}.txt``)."""
    if lang in _extra_cache:
        return _extra_cache[lang]
    path = extra_lexicon_path(lang)
    words: set[str] = set()
    if path is not None:
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            raw = ""
        for line in raw.splitlines():
            item = line.strip()
            if not item or item.startswith("#"):
                continue
            words.add(item.casefold())
    frozen = frozenset(words)
    _extra_cache[lang] = frozen
    return frozen


def dictionary_path(lang: str) -> Path | None:
    for path in dictionary_candidates(lang):
        if path.is_file():
            return path
    return None


def _load_frequency_checker(path: Path) -> Any | None:
    from spellchecker import SpellChecker

    chk = SpellChecker(language=None, local_dictionary=str(path))
    freq = getattr(chk, "word_frequency", None)
    nwords = len(getattr(freq, "dictionary", {}) or {})
    if nwords < 1000:
        return None
    return chk


def _checker(lang: str) -> Any | None:
    if lang == "pt_BR":
        from magiceditor.core.spell_hunspell import dictionary as hunspell_dict

        return hunspell_dict()
    if lang in _cache:
        return _cache[lang]
    chk = None
    path = dictionary_path(lang)
    if path is not None and path.suffix == ".gz":
        try:
            chk = _load_frequency_checker(path)
        except Exception:
            chk = None
    if chk is None:
        code = _CODES.get(lang)
        if code:
            try:
                from spellchecker import SpellChecker

                chk = SpellChecker(language=code)
            except Exception:
                chk = None
    extras = extra_words(lang)
    if chk is not None and extras:
        try:
            chk.word_frequency.load_words(list(extras))
        except Exception:
            pass
    _cache[lang] = chk
    return chk


def backend_available(lang: str) -> bool:
    if lang == "pt_BR":
        from magiceditor.core.spell_hunspell import available

        return available()
    return _checker(lang) is not None


def is_known(word: str, languages: list[str]) -> bool:
    key = word.casefold()
    if not key:
        return True
    for lang in languages:
        if key in extra_words(lang):
            return True
        if lang == "pt_BR":
            from magiceditor.core.spell_hunspell import lookup

            if lookup(word) or lookup(key):
                return True
            continue
        chk = _checker(lang)
        if chk is not None and key in chk:
            return True
    return False


def suggest_words(word: str, languages: list[str], *, limit: int = 6) -> list[str]:
    key = (word or "").strip()
    if not key:
        return []
    ranked: list[str] = []
    seen: set[str] = set()
    for lang in languages:
        if lang == "pt_BR":
            from magiceditor.core.spell_hunspell import suggest as hun_suggest

            for cand in hun_suggest(key, limit=limit):
                c = cand.casefold()
                if not c or c == key.casefold() or c in seen:
                    continue
                seen.add(c)
                ranked.append(cand)
                if len(ranked) >= limit:
                    return ranked
            continue
        chk = _checker(lang)
        if chk is None:
            continue
        fold = key.casefold()
        try:
            best = str(chk.correction(fold) or "").casefold()
        except Exception:
            best = ""
        if best and best != fold and best not in seen:
            seen.add(best)
            ranked.append(best)
        try:
            cands = chk.candidates(fold) or set()
        except Exception:
            cands = set()
        for cand in cands:
            c = str(cand).casefold()
            if not c or c == fold or c in seen:
                continue
            seen.add(c)
            ranked.append(c)
            if len(ranked) >= limit:
                return ranked
        if len(ranked) >= limit:
            return ranked
    return ranked
