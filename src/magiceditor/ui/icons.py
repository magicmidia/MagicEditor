"""Application icons via QtAwesome + Material Design Icons (mdi6).

``qtawesome`` is the de-facto icon toolkit for Qt/Python apps (Font Awesome,
Material Design Icons, etc.). We standardise on **Material Design Icons 6**
(``mdi6.*``) for chrome actions and language/file-type glyphs — large set,
active maintenance, familiar to VS Code / JetBrains users.

Fallback: simple painted glyph if QtAwesome is unavailable (tests / broken env).
"""

from __future__ import annotations

from PyQt6.QtCore import QPointF, QSize, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap

# Semantic action name -> Material Design Icons 6 id
_ACTION_MDI: dict[str, str] = {
    "new": "mdi6.file-plus-outline",
    "open": "mdi6.folder-open-outline",
    "folder": "mdi6.folder-outline",
    "save": "mdi6.content-save-outline",
    "save_as": "mdi6.content-save-edit-outline",
    "print": "mdi6.printer-outline",
    "export_pdf": "mdi6.file-pdf-box",
    "cut": "mdi6.content-cut",
    "copy": "mdi6.content-copy",
    "paste": "mdi6.content-paste",
    "select_all": "mdi6.select-all",
    "find": "mdi6.magnify",
    "find_files": "mdi6.folder-search-outline",
    "quick_open": "mdi6.file-search-outline",
    "replace": "mdi6.find-replace",
    "preview": "mdi6.eye-outline",
    "sidebar": "mdi6.view-sidebar-outline",
    "wrap": "mdi6.wrap",
    "lines": "mdi6.format-list-numbered",
    "zoom_in": "mdi6.magnify-plus-outline",
    "zoom_out": "mdi6.magnify-minus-outline",
    "zoom_reset": "mdi6.magnify-close",
    "fullscreen": "mdi6.fullscreen",
    "exit": "mdi6.exit-to-app",
    "about": "mdi6.information-outline",
    "undo": "mdi6.undo",
    "redo": "mdi6.redo",
    "settings": "mdi6.cog-outline",
    "bookmark": "mdi6.bookmark-outline",
    "goto": "mdi6.ray-start-arrow",
    "tab_close": "mdi6.close",
    "outline": "mdi6.format-list-bulleted-type",
    "indent": "mdi6.format-indent-increase",
    "unindent": "mdi6.format-indent-decrease",
    "duplicate_line": "mdi6.playlist-plus",
    "close_tab": "mdi6.close-box-outline",
}

# Language / file-type -> mdi6 icon (editor market standard set)
_LANG_MDI: dict[str, str] = {
    "python": "mdi6.language-python",
    "javascript": "mdi6.language-javascript",
    "typescript": "mdi6.language-typescript",
    "json": "mdi6.code-json",
    "markdown": "mdi6.language-markdown",
    "html": "mdi6.language-html5",
    "xml": "mdi6.xml",
    "css": "mdi6.language-css3",
    "sql": "mdi6.database-outline",
    "c": "mdi6.language-c",
    "cpp": "mdi6.language-cpp",
    "csharp": "mdi6.language-csharp",
    "java": "mdi6.language-java",
    "go": "mdi6.language-go",
    "rust": "mdi6.language-rust",
    "ruby": "mdi6.language-ruby",
    "php": "mdi6.language-php",
    "shell": "mdi6.console",
    "powershell": "mdi6.powershell",
    "yaml": "mdi6.code-braces",
    "toml": "mdi6.file-code-outline",
    "ini": "mdi6.file-cog-outline",
    "text": "mdi6.file-document-outline",
    "kotlin": "mdi6.language-kotlin",
    "swift": "mdi6.language-swift",
    "lua": "mdi6.language-lua",
    "r": "mdi6.language-r",
    "dart": "mdi6.language-dart",
    "vue": "mdi6.vuejs",
    "svelte": "mdi6.file-code-outline",
    "dockerfile": "mdi6.docker",
    "makefile": "mdi6.file-code-outline",
    "batch": "mdi6.console",
    "graphql": "mdi6.graphql",
    "cmake": "mdi6.file-code-outline",
    "perl": "mdi6.script-text-outline",
    "scala": "mdi6.language-java",
    "haskell": "mdi6.language-haskell",
    "elixir": "mdi6.file-code-outline",
    "erlang": "mdi6.file-code-outline",
    "clojure": "mdi6.file-code-outline",
    "fsharp": "mdi6.language-csharp",
    "vb": "mdi6.language-csharp",
    "objectivec": "mdi6.language-c",
    "matlab": "mdi6.file-code-outline",
    "julia": "mdi6.language-julia",
    "nim": "mdi6.file-code-outline",
    "zig": "mdi6.file-code-outline",
    "solidity": "mdi6.ethereum",
    "terraform": "mdi6.terraform",
    "nginx": "mdi6.nginx",
    "apache": "mdi6.apache",
    "diff": "mdi6.file-compare",
    "git": "mdi6.git",
    "csv": "mdi6.file-delimited-outline",
    "tsv": "mdi6.file-delimited-outline",
    "properties": "mdi6.file-cog-outline",
    "env": "mdi6.file-cog-outline",
    "lock": "mdi6.lock-outline",
    "image": "mdi6.file-image-outline",
    "font": "mdi6.format-font",
    "binary": "mdi6.file-outline",
    "archive": "mdi6.folder-zip-outline",
    "pdf": "mdi6.file-pdf-box",
    "react": "mdi6.react",
    "angular": "mdi6.angular",
    "nodejs": "mdi6.nodejs",
}


def toolbar_icon_color(theme_id: str) -> str:
    return {
        "luminous_void": "#D4D2D0",
        "clean_light": "#334155",
        "midnight_dark": "#A8B8CC",
        "darcula": "#A8B4C0",
        "cobalt_blue": "#B8D4F0",
        "monokai_pro": "#D0CED2",
    }.get(theme_id, "#94A3B8")


def accent_icon_color(theme_id: str) -> str:
    return {
        "luminous_void": "#FFD700",
        "clean_light": "#2563EB",
        "midnight_dark": "#22D3EE",
        "darcula": "#6897BB",
        "cobalt_blue": "#FFCC00",
        "monokai_pro": "#A9DC76",
    }.get(theme_id, "#FFD700")


def _qta_icon(mdi_name: str, color: str, size: int = 24) -> QIcon | None:
    try:
        import qtawesome as qta
    except ImportError:
        return None
    try:
        return qta.icon(mdi_name, color=color, scale_factor=1.0, options=[{"scale_factor": 0.95}])
    except Exception:
        try:
            return qta.icon(mdi_name, color=color)
        except Exception:
            return None


def _fallback_icon(color: str) -> QIcon:
    """Minimal circle glyph when QtAwesome cannot paint."""
    ico = QIcon()
    for s in (16, 20, 24, 32):
        pm = QPixmap(s, s)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pen = QPen(QColor(color))
        pen.setWidthF(max(1.2, s / 12))
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        m = s * 0.22
        p.drawEllipse(QPointF(s / 2, s / 2), s / 2 - m, s / 2 - m)
        p.end()
        ico.addPixmap(pm)
    return ico


def icon(name: str, color: str = "#94A3B8") -> QIcon:
    """Return toolbar/menu icon by semantic *name* (new, save, find, …)."""
    mdi = _ACTION_MDI.get(name, "mdi6.circle-outline")
    ico = _qta_icon(mdi, color)
    return ico if ico is not None and not ico.isNull() else _fallback_icon(color)


def language_icon(lang_id: str, color: str = "#94A3B8") -> QIcon:
    """File-type / language icon for tabs and lists."""
    mdi = _LANG_MDI.get(lang_id, _LANG_MDI["text"])
    ico = _qta_icon(mdi, color)
    return ico if ico is not None and not ico.isNull() else _fallback_icon(color)


def mdi_icon(mdi_name: str, color: str = "#94A3B8") -> QIcon:
    """Direct Material Design Icons access (``mdi6.xxx``)."""
    if not mdi_name.startswith("mdi"):
        mdi_name = f"mdi6.{mdi_name}"
    ico = _qta_icon(mdi_name, color)
    return ico if ico is not None and not ico.isNull() else _fallback_icon(color)


def icon_engine_available() -> bool:
    try:
        import qtawesome  # noqa: F401

        return True
    except ImportError:
        return False
