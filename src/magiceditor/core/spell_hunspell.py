"""Native Brazilian Portuguese Hunspell (LibreOffice VERO).

Dictionary files: ``resources/spell/pt_BR.dic`` + ``pt_BR.aff``
(LGPLv3 / MPL — see README_pt_BR.txt). Checked with pure-Python ``spylls``.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

_lock = threading.Lock()
_dictionary: Any = None
_failed = False
_lookup_cache: dict[str, bool] = {}


def hunspell_stem() -> Path | None:
    """Path without suffix: ``.../resources/spell/pt_BR`` if both files exist."""
    try:
        from magiceditor.paths import resource_root

        stem = resource_root() / "resources" / "spell" / "pt_BR"
    except Exception:
        return None
    if stem.with_suffix(".dic").is_file() and stem.with_suffix(".aff").is_file():
        return stem
    return None


def available() -> bool:
    return hunspell_stem() is not None


def dictionary() -> Any | None:
    """Load the VERO pt_BR dictionary once (thread-safe)."""
    global _dictionary, _failed
    with _lock:
        if _failed:
            return None
        if _dictionary is not None:
            return _dictionary
        stem = hunspell_stem()
        if stem is None:
            _failed = True
            return None
        try:
            from spylls.hunspell import Dictionary

            _dictionary = Dictionary.from_files(str(stem))
        except Exception:
            _failed = True
            _dictionary = None
        return _dictionary


def preload() -> None:
    dictionary()


def clear_cache() -> None:
    global _dictionary, _failed
    with _lock:
        _dictionary = None
        _failed = False
        _lookup_cache.clear()


def lookup(word: str) -> bool:
    if not word:
        return False
    cached = _lookup_cache.get(word)
    if cached is not None:
        return cached
    d = dictionary()
    if d is None:
        return False
    found = bool(d.lookup(word))
    if not found:
        folded = word.casefold()
        found = folded != word and bool(d.lookup(folded))
    if len(_lookup_cache) > 20000:
        _lookup_cache.clear()
    _lookup_cache[word] = found
    return found


def suggest(word: str, *, limit: int = 6) -> list[str]:
    d = dictionary()
    key = (word or "").strip()
    if d is None or not key:
        return []
    out: list[str] = []
    seen: set[str] = set()
    try:
        raw = list(d.suggest(key))
    except Exception:
        raw = []
    if key != key.casefold():
        try:
            raw.extend(d.suggest(key.casefold()))
        except Exception:
            pass
    for cand in raw:
        c = str(cand).strip()
        if not c or c.casefold() == key.casefold() or c.casefold() in seen:
            continue
        seen.add(c.casefold())
        out.append(c)
        if len(out) >= limit:
            break
    return out
