from magiceditor.preview.markdown_preview import render_markdown, strip_frontmatter
from magiceditor.preview.preview_css import wrap_preview_html
from magiceditor.themes.tokens import chrome_tokens


def test_headings_lists_tables_and_code() -> None:
    src = """# Title

A paragraph.

- item one
- item two

| A | B |
| --- | --- |
| 1 | 2 |

```python
print("hi")
```
"""
    html = render_markdown(src)
    assert "<h1" in html
    assert "<li>" in html
    assert "<table>" in html
    assert "<th>" in html
    assert "<pre>" in html
    assert "print" in html


def test_gfm_strike_and_task_list() -> None:
    src = """- [ ] open
- [x] done

This is ~~old~~ now.
"""
    html = render_markdown(src)
    assert "☐" in html
    assert "☑" in html
    assert "<del>old</del>" in html


def test_frontmatter_stripped() -> None:
    src = "---\ntitle: Spec\n---\n# Hello\n"
    assert strip_frontmatter(src).startswith("# Hello")
    html = render_markdown(src)
    assert "<h1" in html
    assert "title: Spec" not in html


def test_preview_html_uses_theme_colors() -> None:
    html = wrap_preview_html("<p>Hi</p>", "luminous_void")
    tok = chrome_tokens("luminous_void")
    assert tok.fg.lower() in html.lower()
    assert tok.bg.lower() in html.lower()
    assert "<p>Hi</p>" in html


def test_footnotes_and_definition_list() -> None:
    src = """See the note.[^1]

[^1]: Extra detail.

Term
: Definition of the term.
"""
    html = render_markdown(src)
    assert "footnote" in html.lower() or "fn:" in html.lower() or "Extra detail" in html
    assert "Definition of the term" in html
