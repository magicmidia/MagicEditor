"""Icon packs for MagicEditor chrome and file types.

Packs
-----
* **qlementine** — `oclero/qlementine-icons` (MIT), modern Qt desktop set
  https://oclero.github.io/qlementine-icons/ — bundled as SVG under
  ``resources/icons/qlementine/``.
* **material** — Material Design Icons 6 via QtAwesome (``mdi6.*``), outline
  style suitable for light & dark chrome (\"Material Light/outline\").

Switch at runtime via :func:`set_icon_pack` (Settings → Appearance).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PyQt6.QtCore import QByteArray, QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap

from magiceditor.paths import resource_root

# Current pack: "qlementine" | "material"
_icon_pack: str = "qlementine"

ICON_PACKS: list[tuple[str, str]] = [
    ("qlementine", "Qlementine (Qt)"),
    ("material", "Material Design (outline)"),
]

# Semantic action → Qlementine SVG basename (no .svg)
_ACTION_QLEMENTINE: dict[str, str] = {
    "new": "add-file",
    "open": "folder-open",
    "folder": "folder",
    "save": "save",
    "save_as": "save-to-disk",
    "print": "print",
    "export_pdf": "pdf",
    "cut": "cut",
    "copy": "copy",
    "paste": "paste",
    "select_all": "check-multiple",
    "find": "search",
    "find_files": "file-manager",
    "quick_open": "file",
    "replace": "replace",
    "preview": "eye",
    "sidebar": "items-tree",
    "wrap": "text",
    "lines": "items-list",
    "zoom_in": "zoom-in",
    "zoom_out": "zoom-out",
    "zoom_reset": "zoom-original",
    "fullscreen": "fullscreen",
    "exit": "log-out",
    "about": "info",
    "undo": "undo",
    "redo": "redo",
    "settings": "settings",
    "bookmark": "bookmark",
    "goto": "jump",
    "tab_close": "close-small",
    "outline": "items-list",
    "indent": "indent-more",
    "unindent": "indent-less",
    "duplicate_line": "duplicate",
    "close_tab": "close-single",
    "close_others": "close-single",
    "close_all": "close-all",
    "move_up": "arrow-up",
    "move_down": "arrow-down",
    "sort": "sort-alpha-asc",
    "join": "gather",
    "delete_lines": "trash",
    "trim": "erase",
    "tabs_spaces": "spacing-horizontal",
    "spaces_tabs": "spacing-vertical",
    "comment": "comment",
    "add_cursor": "plus-small",
    "select_occurrences": "check-multiple",
    "clear_cursors": "clear",
    "brace": "link",
    "goto_anything": "search",
    "palette": "menu-burger",
    "bookmark_next": "chevron-down",
    "bookmark_prev": "chevron-up",
    "symbols": "items-list",
    "reload": "refresh",
    "reveal": "external-link",
    "copy_path": "copy",
    "copy_dir": "folder",
    "compare": "swap",
    "split": "ui-panels-left-right",
    "spell": "book",
    "spell_ignore": "forbidden",
    "spell_add": "book-open",
    "minimap": "ui-panel-right",
    "performance": "gauge-middle",
    "browser": "globe",
    "cancel_search": "close",
    "export_theme": "export",
    "import_theme": "download",
    "recent": "open-recent",
    "encoding": "font",
    "eol": "paragraph",
    "theme": "paint-palette",
    "language": "globe",
    "save_all": "save",
    "case_upper": "case-uppercase",
    "case_lower": "case-lowercase",
    "case_title": "case-title",
    "case_sentence": "case-default",
    "case_invert": "case-small-caps",
    "b64_encode": "lock",
    "b64_decode": "unlock",
    "url_encode": "link",
    "url_decode": "external-link",
    "remove_duplicates": "erase",
    "remove_consecutive": "clear",
    "reverse_lines": "rotate-anticlockwise",
    "sort_length": "sort-asc",
    "insert_datetime": "calendar",
    "insert_date": "calendar",
    "insert_timestamp": "clock",
    "checksum": "file-text",
    "doc_stats": "gauge-high",
    "filter": "filter",
    "log_summary": "gauge-middle",
    "always_on_top": "pin-fill",
    "read_only": "lock",
}

# Semantic action → Material Design Icons 6
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
    "close_others": "mdi6.close-box-outline",
    "close_all": "mdi6.close-box-multiple-outline",
    "move_up": "mdi6.arrow-up",
    "move_down": "mdi6.arrow-down",
    "sort": "mdi6.sort-alphabetical-ascending",
    "join": "mdi6.arrow-collapse-vertical",
    "delete_lines": "mdi6.delete-outline",
    "trim": "mdi6.content-cut",
    "tabs_spaces": "mdi6.keyboard-space",
    "spaces_tabs": "mdi6.keyboard-tab",
    "comment": "mdi6.comment-outline",
    "add_cursor": "mdi6.cursor-default-click-outline",
    "select_occurrences": "mdi6.select-search",
    "clear_cursors": "mdi6.cursor-default-outline",
    "brace": "mdi6.code-brackets",
    "goto_anything": "mdi6.magnify",
    "palette": "mdi6.console-line",
    "bookmark_next": "mdi6.chevron-down",
    "bookmark_prev": "mdi6.chevron-up",
    "symbols": "mdi6.symbol",
    "reload": "mdi6.refresh",
    "reveal": "mdi6.folder-open-outline",
    "copy_path": "mdi6.link-variant",
    "copy_dir": "mdi6.folder-outline",
    "compare": "mdi6.file-compare",
    "split": "mdi6.view-split-vertical",
    "spell": "mdi6.spellcheck",
    "spell_ignore": "mdi6.minus-circle-outline",
    "spell_add": "mdi6.book-plus-outline",
    "minimap": "mdi6.map-outline",
    "performance": "mdi6.speedometer",
    "browser": "mdi6.web",
    "cancel_search": "mdi6.close-circle-outline",
    "export_theme": "mdi6.export",
    "import_theme": "mdi6.import",
    "recent": "mdi6.history",
    "encoding": "mdi6.alphabetical",
    "eol": "mdi6.keyboard-return",
    "theme": "mdi6.palette-outline",
    "language": "mdi6.translate",
    "save_all": "mdi6.content-save-all-outline",
    "case_upper": "mdi6.format-letter-case-upper",
    "case_lower": "mdi6.format-letter-case-lower",
    "case_title": "mdi6.format-title",
    "case_sentence": "mdi6.format-letter-case",
    "case_invert": "mdi6.invert-colors",
    "b64_encode": "mdi6.lock-outline",
    "b64_decode": "mdi6.lock-open-outline",
    "url_encode": "mdi6.link-variant",
    "url_decode": "mdi6.link-variant-off",
    "remove_duplicates": "mdi6.delete-sweep-outline",
    "remove_consecutive": "mdi6.filter-remove-outline",
    "reverse_lines": "mdi6.sort-reverse-variant",
    "sort_length": "mdi6.sort-numeric-ascending",
    "insert_datetime": "mdi6.calendar-clock",
    "insert_date": "mdi6.calendar-outline",
    "insert_timestamp": "mdi6.clock-outline",
    "checksum": "mdi6.fingerprint",
    "doc_stats": "mdi6.chart-box-outline",
    "filter": "mdi6.filter-outline",
    "log_summary": "mdi6.chart-timeline-variant",
    "always_on_top": "mdi6.pin-outline",
    "read_only": "mdi6.lock-outline",
}

# Language → Qlementine (generic file kinds where specific lang glyphs missing)
_LANG_QLEMENTINE: dict[str, str] = {
    "python": "file-script",
    "javascript": "file-script",
    "typescript": "file-script",
    "json": "code-markup",
    "markdown": "file-markdown",
    "html": "file-html",
    "xml": "code-markup",
    "css": "code-markup",
    "sql": "database",
    "c": "file-script",
    "cpp": "file-script",
    "csharp": "file-script",
    "java": "file-script",
    "go": "file-script",
    "rust": "file-script",
    "ruby": "file-script",
    "php": "file-script",
    "shell": "command-line",
    "powershell": "command-line",
    "yaml": "code-markup",
    "toml": "code-markup",
    "ini": "settings",
    "text": "file-text",
    "kotlin": "file-script",
    "swift": "file-script",
    "lua": "file-script",
    "r": "file-script",
    "dart": "file-script",
    "vue": "file-html",
    "svelte": "file-html",
    "dockerfile": "file-script",
    "makefile": "build",
    "batch": "command-line",
    "graphql": "code-markup",
    "cmake": "build",
    "pdf": "pdf",
    "csv": "file-text",
    "git": "file",
    "lock": "lock",
    "image": "media",
    "archive": "archive",
    "binary": "executable",
    "font": "font",
    "env": "settings",
    "properties": "settings",
    "diff": "items-list",
}

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
    "pdf": "mdi6.file-pdf-box",
    "csv": "mdi6.file-delimited-outline",
    "git": "mdi6.git",
    "lock": "mdi6.lock-outline",
    "image": "mdi6.file-image-outline",
    "archive": "mdi6.folder-zip-outline",
    "binary": "mdi6.file-outline",
    "font": "mdi6.format-font",
    "env": "mdi6.file-cog-outline",
    "properties": "mdi6.file-cog-outline",
    "diff": "mdi6.file-compare",
}


def set_icon_pack(pack: str) -> None:
    """Set active pack: ``qlementine`` or ``material``."""
    global _icon_pack
    pack = (pack or "qlementine").strip().lower()
    if pack not in {"qlementine", "material"}:
        pack = "qlementine"
    if pack != _icon_pack:
        _icon_pack = pack
        icon.cache_clear()  # type: ignore[attr-defined]
        language_icon.cache_clear()  # type: ignore[attr-defined]
        _qlementine_index.cache_clear()


def get_icon_pack() -> str:
    return _icon_pack


def toolbar_icon_color(theme_id: str) -> str:
    return {
        "luminous_void": "#D4D2D0",
        "clean_light": "#334155",
        "midnight_dark": "#A8B8CC",
        "darcula": "#A8B4C0",
        "cobalt_blue": "#B8D4F0",
        "monokai_pro": "#D0CED2",
        "tokyo_night": "#C0CAF5",
        "catppuccin_mocha": "#CDD6F4",
        "nord": "#D8DEE9",
        "rose_pine": "#E0DEF4",
    }.get(theme_id, "#94A3B8")


def accent_icon_color(theme_id: str) -> str:
    return {
        "luminous_void": "#FFD700",
        "clean_light": "#2563EB",
        "midnight_dark": "#22D3EE",
        "darcula": "#6897BB",
        "cobalt_blue": "#FFCC00",
        "monokai_pro": "#A9DC76",
        "tokyo_night": "#7AA2F7",
        "catppuccin_mocha": "#CBA6F7",
        "nord": "#88C0D0",
        "rose_pine": "#EBBCBA",
    }.get(theme_id, "#FFD700")


def icons_dir() -> Path:
    return resource_root() / "resources" / "icons" / "qlementine"


@lru_cache(maxsize=1)
def _qlementine_index() -> dict[str, Path]:
    """Map basename → path for bundled Qlementine SVGs."""
    root = icons_dir()
    out: dict[str, Path] = {}
    if not root.is_dir():
        return out
    for path in root.rglob("*.svg"):
        out[path.stem] = path
    return out


def _recolor_svg(svg: str, color: str) -> bytes:
    """Force monochrome SVG paths to *color* (Qlementine uses fill=#000)."""
    c = color if color.startswith("#") else f"#{color}"
    text = svg
    for black in ('fill="#000"', "fill='#000'", 'fill="#000000"', "fill='#000000'"):
        text = text.replace(black, f'fill="{c}"')
    # Some assets use fill: #000 in style=
    text = text.replace("fill:#000", f"fill:{c}").replace("fill: #000", f"fill: {c}")
    return text.encode("utf-8")


def _svg_to_icon(svg_path: Path, color: str) -> QIcon | None:
    try:
        from PyQt6.QtSvg import QSvgRenderer
    except ImportError:
        return None
    try:
        raw = svg_path.read_text(encoding="utf-8")
    except OSError:
        return None
    data = _recolor_svg(raw, color)
    renderer = QSvgRenderer(QByteArray(data))
    if not renderer.isValid():
        return None
    ico = QIcon()
    for logical in (16, 18, 20, 22, 24, 28, 32):
        px = logical * 2  # HiDPI
        pm = QPixmap(px, px)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        # Slight padding for 16px-designed glyphs at larger sizes
        margin = max(1, px // 16)
        renderer.render(p, QRectF(margin, margin, px - 2 * margin, px - 2 * margin))
        p.end()
        ico.addPixmap(pm)
    return ico


def _qta_icon(mdi_name: str, color: str) -> QIcon | None:
    try:
        import qtawesome as qta
    except ImportError:
        return None
    try:
        return qta.icon(mdi_name, color=color)
    except Exception:
        return None


def _fallback_icon(color: str) -> QIcon:
    ico = QIcon()
    for s in (16, 20, 24, 32):
        pm = QPixmap(s, s)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pen = QPen(QColor(color))
        pen.setWidthF(max(1.2, s / 12))
        p.setPen(pen)
        m = s * 0.22
        p.drawEllipse(QPointF(s / 2, s / 2), s / 2 - m, s / 2 - m)
        p.end()
        ico.addPixmap(pm)
    return ico


@lru_cache(maxsize=256)
def icon(name: str, color: str = "#94A3B8") -> QIcon:
    """Toolbar/menu icon by semantic *name*."""
    pack = _icon_pack
    if pack == "material":
        mdi = _ACTION_MDI.get(name, "mdi6.circle-outline")
        ico = _qta_icon(mdi, color)
        if ico is not None and not ico.isNull():
            return ico
    # qlementine (default) — with material fallback
    qname = _ACTION_QLEMENTINE.get(name, "file")
    path = _qlementine_index().get(qname)
    if path is not None:
        ico = _svg_to_icon(path, color)
        if ico is not None and not ico.isNull():
            return ico
    mdi = _ACTION_MDI.get(name, "mdi6.circle-outline")
    ico = _qta_icon(mdi, color)
    return ico if ico is not None and not ico.isNull() else _fallback_icon(color)


@lru_cache(maxsize=128)
def language_icon(lang_id: str, color: str = "#94A3B8") -> QIcon:
    """File-type / language icon for tabs."""
    pack = _icon_pack
    if pack == "material":
        mdi = _LANG_MDI.get(lang_id, _LANG_MDI["text"])
        ico = _qta_icon(mdi, color)
        if ico is not None and not ico.isNull():
            return ico
    qname = _LANG_QLEMENTINE.get(lang_id, "file-text")
    path = _qlementine_index().get(qname)
    if path is not None:
        ico = _svg_to_icon(path, color)
        if ico is not None and not ico.isNull():
            return ico
    mdi = _LANG_MDI.get(lang_id, _LANG_MDI["text"])
    ico = _qta_icon(mdi, color)
    return ico if ico is not None and not ico.isNull() else _fallback_icon(color)


def icon_engine_info() -> str:
    n = len(_qlementine_index())
    try:
        import qtawesome  # noqa: F401

        mdi = "yes"
    except ImportError:
        mdi = "no"
    return f"pack={_icon_pack} qlementine_svgs={n} qtawesome={mdi}"
