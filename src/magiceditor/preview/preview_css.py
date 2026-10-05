"""Qt-friendly CSS for the Markdown/HTML preview pane."""

from __future__ import annotations

from magiceditor.themes.tokens import chrome_tokens


def preview_css(theme_id: str) -> str:
    t = chrome_tokens(theme_id)
    return f"""
body {{
  color: {t.fg};
  background-color: {t.bg};
  font-family: 'Segoe UI', 'Cascadia Code', sans-serif;
  font-size: 11pt;
  line-height: 1.55;
  padding: 16px 20px;
}}
h1, h2, h3, h4, h5, h6 {{
  color: {t.heading};
  margin-top: 1.15em;
  margin-bottom: 0.4em;
}}
p, li, td, th, blockquote {{ color: {t.fg}; }}
a {{ color: {t.link}; }}
hr {{ border: none; border-top: 1px solid {t.border}; }}
blockquote {{
  color: {t.muted};
  margin-left: 0;
  padding-left: 12px;
  border-left: 3px solid {t.accent};
}}
code, pre {{
  font-family: 'Cascadia Code', Consolas, monospace;
  background-color: {t.code_bg};
  color: {t.fg};
}}
code {{ padding: 1px 4px; }}
pre {{ padding: 12px; }}
table {{ border-collapse: collapse; margin: 10px 0; }}
th, td {{
  border: 1px solid {t.border};
  padding: 4px 8px;
  color: {t.fg};
}}
th {{ background-color: {t.code_bg}; color: {t.heading}; }}
del {{ color: {t.muted}; }}
img {{ max-width: 100%; }}
""".strip()


def wrap_preview_html(body: str, theme_id: str) -> str:
    """Return the body fragment. Theme CSS is applied with setDefaultStyleSheet.

    Embedding ``<style>`` made QTextBrowser paint the rules as text: the
    sanitizer removes the tag and leaves the CSS body behind.
    """
    _ = theme_id
    return body
