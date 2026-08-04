from magiceditor.core.symbols import extract_symbols


def test_python_symbols() -> None:
    src = "class Foo:\n    def bar(self):\n        pass\n\ndef baz():\n    pass\n"
    syms = extract_symbols(src, "python")
    names = {s.name for s in syms}
    assert "Foo" in names
    assert "bar" in names
    assert "baz" in names


def test_markdown_headings() -> None:
    src = "# Title\n\n## Sub\n"
    syms = extract_symbols(src, "markdown")
    assert syms[0].name == "Title"
    assert syms[0].kind == "h1"
