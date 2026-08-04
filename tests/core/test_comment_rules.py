from magiceditor.core.comment_rules import comment_style_for, toggle_line_comments


def test_python_toggle_comment() -> None:
    style = comment_style_for("python")
    assert style.line == "#"
    lines = ["def foo():", "    return 1"]
    commented = toggle_line_comments(lines, "python")
    assert all(ln.lstrip().startswith("#") for ln in commented if ln.strip())
    restored = toggle_line_comments(commented, "python")
    assert restored == lines


def test_js_comment_style() -> None:
    assert comment_style_for("javascript").line == "//"
    out = toggle_line_comments(["const x = 1;"], "js")
    assert out[0].startswith("//")
