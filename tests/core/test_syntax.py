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
    assert language_label("log") == "Log"


def test_detect_log_extension() -> None:
    assert detect_language("server.log") == "log"


def test_tokenize_log_severities() -> None:
    spans = tokenize_line("2026-09-01 10:00:00 ERROR disk full", "log")
    kinds = [k for _, _, k in spans]
    assert "log_error" in kinds
    # The ERROR span covers the keyword itself.
    err = next(s for s in spans if s[2] == "log_error")
    assert "2026-09-01 10:00:00 ERROR disk full"[err[0] : err[0] + err[1]] == "ERROR"


def test_tokenize_log_all_levels_and_no_false_positive() -> None:
    cases = {
        "[WARN] x": "log_warn",
        "INFO: y": "log_info",
        "DEBUG detail": "log_debug",
        "Traceback (most recent call last):": "log_error",
    }
    for line, kind in cases.items():
        kinds = {k for _, _, k in tokenize_line(line, "log")}
        assert kind in kinds, line
    assert tokenize_line("information processed", "log") == []



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
