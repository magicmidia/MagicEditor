"""Syntax detect + tokenize tests."""

from __future__ import annotations

from magiceditor.core.syntax.detect import detect_language, language_label
from magiceditor.core.syntax.rules import tokenize_line


def test_detect_reads_extensions_json() -> None:
    """J1.7: detect_language uses the shipped extensions.json catalog."""
    import json
    from pathlib import Path

    from magiceditor.core.syntax.detect import _catalog

    data = json.loads(Path("resources/syntax/extensions.json").read_text(encoding="utf-8"))
    ext, lang = next(iter(data["extensions"].items()))
    loaded, _bases = _catalog()
    assert loaded[ext] == lang
    assert detect_language(f"file.{ext}") == lang


def test_detect_python() -> None:
    assert detect_language("app.py") == "python"
    assert detect_language(None, "main.js") == "javascript"
    assert detect_language("notes.txt") == "text"


def test_tokenize_python_keywords() -> None:
    spans = tokenize_line("def hello():  # hi", "python")
    kinds = {k for _, _, k in spans}
    assert "keyword" in kinds
    assert "comment" in kinds


def test_tokenize_string() -> None:
    spans = tokenize_line('x = "abc"', "python")
    assert any(k == "string" for _, _, k in spans)


def test_language_label() -> None:
    assert language_label("python") == "Python"


def test_tokenize_does_not_allocate_claimed_and_caches_rules() -> None:
    from magiceditor.core.syntax import rules as rules_mod

    rules_mod.clear_rules_cache()
    first = rules_mod.rules_for("python")
    second = rules_mod.rules_for("python")
    assert first is second
    spans = rules_mod.tokenize_line("def x(): # c", "python")
    kinds = [k for _, _, k in spans]
    assert "keyword" in kinds
    assert "comment" in kinds
