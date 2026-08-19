"""Full-language dictionaries (pyspellchecker) behind SpellEngine.

Looks for bundled ``resources/spell/{en,pt,es}.json.gz`` first so the
onefile EXE does not depend on ``pkgutil.get_data`` (which misses
extracted datas). Falls back to the installed package.
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


def dictionary_candidates(lang: str) -> list[Path]:
    """Search paths for ``pt.json.gz`` / ``en.json.gz`` / ``es.json.gz``."""
    code = _CODES.get(lang)
    if not code:
        return []
    name = f"{code}.json.gz"
    out: list[Path] = []
    try:
        from magiceditor.paths import resource_root

        root = resource_root()
        out.append(root / "resources" / "spell" / name)
        out.append(root / "spellchecker" / "resources" / name)
    except Exception:
        pass
    try:
        import spellchecker as sc

        pkg = Path(sc.__file__).resolve().parent
        out.append(pkg / "resources" / name)
    except Exception:
        pass
    return out


def dictionary_path(lang: str) -> Path | None:
    for path in dictionary_candidates(lang):
        if path.is_file():
            return path
    return None


def _checker(lang: str) -> Any | None:
    if lang in _cache:
        return _cache[lang]
    chk = None
    path = dictionary_path(lang)
    if path is not None:
        try:
            from spellchecker import SpellChecker

            chk = SpellChecker(language=None, local_dictionary=str(path))
            freq = getattr(chk, "word_frequency", None)
            nwords = len(getattr(freq, "dictionary", {}) or {})
            if nwords < 1000:
                chk = None
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
    _cache[lang] = chk
    return chk


def backend_available(lang: str) -> bool:
    return _checker(lang) is not None


def is_known(word: str, languages: list[str]) -> bool:
    key = word.casefold()
    if not key:
        return True
    for lang in languages:
        chk = _checker(lang)
        if chk is not None and key in chk:
            return True
    return False


def suggest_words(word: str, languages: list[str], *, limit: int = 6) -> list[str]:
    key = (word or "").strip().casefold()
    if not key:
        return []
    ranked: list[str] = []
    seen: set[str] = set()
    for lang in languages:
        chk = _checker(lang)
        if chk is None:
            continue
        try:
            best = str(chk.correction(key) or "").casefold()
        except Exception:
            best = ""
        if best and best != key and best not in seen:
            seen.add(best)
            ranked.append(best)
        try:
            cands = chk.candidates(key) or set()
        except Exception:
            cands = set()
        for cand in cands:
            c = str(cand).casefold()
            if not c or c == key or c in seen:
                continue
            seen.add(c)
            ranked.append(c)
            if len(ranked) >= limit:
                return ranked
        if len(ranked) >= limit:
            return ranked
    return ranked
