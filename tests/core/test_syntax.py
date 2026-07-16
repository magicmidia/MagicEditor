"""Syntax detect + tokenize tests."""

from __future__ import annotations

from magiceditor.core.syntax.detect import detect_language, language_label
from magiceditor.core.syntax.rules import tokenize_line


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
