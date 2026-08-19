from magiceditor.core.indent import (
    extra_indent_after,
    indent_unit,
    leading_whitespace,
    newline_auto_indent,
    unindent_prefix,
)


def test_indent_unit_spaces_and_tab() -> None:
    assert indent_unit(spaces=True, width=4) == "    "
    assert indent_unit(spaces=False, width=4) == "\t"


def test_leading_whitespace() -> None:
    assert leading_whitespace("    def x") == "    "
    assert leading_whitespace("\tfoo") == "\t"
    assert leading_whitespace("x") == ""


def test_newline_auto_indent_python_block() -> None:
    unit = indent_unit(spaces=True, width=4)
    assert newline_auto_indent("def foo():", "python", unit) == "    "
    assert newline_auto_indent("    if x:", "python", unit) == "        "
    assert newline_auto_indent("    x = 1", "python", unit) == "    "


def test_extra_indent_braces() -> None:
    unit = "    "
    assert extra_indent_after("if (x) {", "javascript", unit) == unit
    assert extra_indent_after("foo()", "javascript", unit) == ""


def test_unindent_prefix() -> None:
    assert unindent_prefix("    x", 4) == 4
    assert unindent_prefix("\tx", 4) == 1
    assert unindent_prefix("x", 4) == 0
