"""Generate modern editor-inspired QSS skins from a shared chrome template."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "resources" / "themes"


def _rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgba(hex_color: str, alpha: int) -> str:
    r, g, b = _rgb(hex_color)
    return f"rgba({r}, {g}, {b}, {alpha})"


# Distinct palettes used in VS Code / Neovim / Zed (not clones of existing ME skins).
SKINS: dict[str, dict[str, str]] = {
    "tokyo_night": {
        "comment": "Tokyo Night — enkia/tokyo-night (VS Code, Neovim)",
        "window": "#16161e",
        "chrome": "#1a1b26",
        "surface": "#1f2335",
        "canvas": "#1a1b26",
        "input": "#24283b",
        "fg": "#c0caf5",
        "muted": "#565f89",
        "heading": "#c0caf5",
        "accent": "#7aa2f7",
        "on_accent": "#16161e",
        "danger": "#f7768e",
        "border": "#292e42",
    },
    "catppuccin_mocha": {
        "comment": "Catppuccin Mocha — catppuccin/catppuccin",
        "window": "#181825",
        "chrome": "#1e1e2e",
        "surface": "#313244",
        "canvas": "#1e1e2e",
        "input": "#313244",
        "fg": "#cdd6f4",
        "muted": "#6c7086",
        "heading": "#cdd6f4",
        "accent": "#cba6f7",
        "on_accent": "#1e1e2e",
        "danger": "#f38ba8",
        "border": "#45475a",
    },
    "nord": {
        "comment": "Nord — arctic ice palette (nordtheme)",
        "window": "#2E3440",
        "chrome": "#3B4252",
        "surface": "#434C5E",
        "canvas": "#2E3440",
        "input": "#3B4252",
        "fg": "#ECEFF4",
        "muted": "#7B88A1",
        "heading": "#ECEFF4",
        "accent": "#88C0D0",
        "on_accent": "#2E3440",
        "danger": "#BF616A",
        "border": "#4C566A",
    },
    "rose_pine": {
        "comment": "Rosé Pine — rosepinetheme (Neovim, VS Code, Zed)",
        "window": "#191724",
        "chrome": "#1f1d2e",
        "surface": "#26233a",
        "canvas": "#191724",
        "input": "#26233a",
        "fg": "#e0def4",
        "muted": "#6e6a86",
        "heading": "#e0def4",
        "accent": "#ebbcba",
        "on_accent": "#191724",
        "danger": "#eb6f92",
        "border": "#403d52",
    },
}


TEMPLATE = """\
/* {comment} */
QMainWindow {{
  background-color: {window};
  color: {fg};
}}
QWidget {{
  color: {fg};
}}
QMenuBar {{
  background-color: {chrome};
  color: {fg};
  border-bottom: 1px solid {border};
  padding: 2px 12px;
  spacing: 0px;
  min-height: 28px;
}}
QMenuBar::item {{
  background: transparent;
  color: {muted};
  padding: 4px 10px;
  margin: 0px 2px;
  border-radius: 4px;
}}
QMenuBar::item:selected,
QMenuBar::item:pressed {{
  background-color: {accent_a18};
  color: {heading};
}}
QMenu {{
  background-color: {surface};
  color: {fg};
  border: 1px solid {border};
  border-radius: 6px;
  padding: 2px;
}}
QMenu::item {{
  background: transparent;
  color: {fg};
  padding: 3px 28px 3px 24px;
  margin: 0px;
  border-radius: 3px;
}}
QMenu::item:selected {{
  background-color: {accent_a28};
  color: {heading};
}}
QMenu::item:checked {{
  color: {accent};
}}
QMenu::indicator {{
  width: 12px;
  height: 12px;
  left: 6px;
}}
QMenu::indicator:checked {{
  background-color: {accent};
  border-radius: 2px;
}}
QMenu::separator {{
  height: 1px;
  background: {border};
  margin: 3px 6px;
}}
QToolBar {{
  background-color: {chrome};
  border: none;
  border-bottom: 1px solid {border};
  spacing: 2px;
  padding: 4px 12px;
  min-height: 36px;
}}
QToolBar::separator {{
  background: {border};
  width: 1px;
  margin: 6px 6px;
}}
QToolButton {{
  background-color: transparent;
  color: {muted};
  border: 1px solid transparent;
  border-radius: 4px;
  padding: 5px;
  min-width: 28px;
  min-height: 28px;
}}
QToolButton:hover {{
  background-color: {accent_a14};
  color: {heading};
}}
QToolButton:pressed,
QToolButton:checked {{
  background-color: {accent_a36};
  border-color: {accent_a80};
  color: {accent};
}}
QStatusBar {{
  background-color: {chrome};
  color: {muted};
  border-top: 1px solid {border};
  min-height: 26px;
  padding: 0px 4px;
}}
QStatusBar QLabel {{
  color: {muted};
  background: transparent;
  padding: 0px 8px;
}}
QStatusBar QLabel#statusAccent,
QStatusBar QLabel#statusVersion {{
  color: {accent};
  font-weight: 600;
}}
QDockWidget {{
  color: {fg};
  background-color: {surface};
  border: none;
}}
QDockWidget::title {{
  background-color: {chrome};
  color: {heading};
  padding: 8px 12px;
  border-bottom: 1px solid {border};
  text-align: left;
  font-weight: 600;
}}
QWidget#workspaceSidebar {{
  background-color: {surface};
  border-right: 1px solid {border};
}}
QFrame#sidebarHeader {{
  background-color: {chrome};
  border-bottom: 1px solid {border};
}}
QLabel#sidebarWorkspaceTitle {{
  color: {heading};
  font-weight: 600;
  font-size: 12px;
}}
QLabel#sidebarWorkspaceSub,
QLabel#sidebarSectionLabel {{
  color: {muted};
  font-size: 9px;
  font-weight: 600;
}}
QLabel#sidebarWorkspaceBadge {{
  background-color: {accent_a40};
  color: {accent};
  border: 1px solid {accent_a80};
  border-radius: 12px;
}}
QPushButton#sidebarNavButton {{
  text-align: left;
  padding: 6px 10px;
  border: none;
  border-radius: 4px;
  color: {muted};
  background: transparent;
}}
QPushButton#sidebarNavButton:hover {{
  background-color: {accent_a14};
  color: {heading};
}}
QPushButton#sidebarNavButton:checked {{
  background-color: {accent_a22};
  color: {accent};
  border: 1px solid {accent_a50};
}}
QListWidget#sidebarOpenEditors,
QTreeView#sidebarTree {{
  background-color: transparent;
  border: none;
  outline: none;
  color: {fg};
}}
QListWidget#sidebarOpenEditors::item {{
  padding: 4px 6px;
  border-radius: 4px;
  color: {fg};
}}
QListWidget#sidebarOpenEditors::item:selected,
QListWidget#sidebarOpenEditors::item:hover {{
  background-color: {accent_a28};
  color: {accent};
}}
QLineEdit#toolbarSearch {{
  background-color: {input};
  color: {fg};
  border: 1px solid {border};
  border-radius: 4px;
  padding: 4px 10px;
  min-height: 18px;
}}
QLineEdit#toolbarSearch:hover,
QLineEdit#toolbarSearch:focus {{
  border: 1px solid {accent};
}}
QDialog#quickOpenDialog {{
  background-color: {surface};
}}
QLineEdit#quickOpenInput {{
  background-color: {input};
  border: 1px solid {accent};
  border-radius: 4px;
  padding: 8px 12px;
}}
QListWidget#quickOpenList {{
  background-color: {chrome};
  border: 1px solid {border};
  border-radius: 4px;
}}
QListWidget#quickOpenList::item:selected {{
  background-color: {accent_a40};
  color: {heading};
}}
QTabWidget {{
  background-color: {chrome};
}}
QTabWidget::pane {{
  border: none;
  background-color: {canvas};
  top: 0px;
}}
QTabBar {{
  background-color: {chrome};
  qproperty-drawBase: 0;
}}
QTabBar::tab {{
  background-color: transparent;
  color: {muted};
  border: none;
  border-bottom: 2px solid transparent;
  border-top-left-radius: 4px;
  border-top-right-radius: 4px;
  min-width: 72px;
  max-width: 220px;
  padding: 3px 12px 3px 10px;
  margin-right: 1px;
  min-height: 18px;
}}
QTabBar::tab:selected {{
  background-color: {canvas};
  color: {heading};
  border-bottom: 2px solid {accent};
}}
QTabBar::tab:hover:!selected {{
  color: {heading};
  background-color: {accent_a14};
}}
QTabBar QToolButton,
QToolButton#tabScrollButton,
QToolButton#tabNewButton,
QToolButton#tabCloseButton {{
  background: transparent;
  color: {muted};
  border: none;
  border-radius: 3px;
}}
QToolButton#tabCloseButton:hover {{
  background-color: {danger};
  color: {heading};
}}
QToolButton#tabNewButton:hover,
QToolButton#tabScrollButton:hover {{
  background: {accent_a28};
  color: {accent};
}}
QWidget#tabCornerLeft, QWidget#tabCornerRight {{
  background-color: {chrome};
}}
QListWidget#settingsNav {{
  background: {chrome};
  border: none;
  color: {muted};
  padding: 8px 4px;
}}
QListWidget#settingsNav::item {{
  padding: 10px 12px;
  border-radius: 6px;
  margin: 2px 4px;
}}
QListWidget#settingsNav::item:selected {{
  background: {accent_a22};
  color: {accent};
}}
QDialog#settingsDialog {{
  background: {canvas};
}}
QPlainTextEdit,
QTextEdit,
QTextBrowser,
QTextBrowser#markdownPreview {{
  background-color: {canvas};
  color: {fg};
  border: none;
  selection-background-color: {accent_a55};
  selection-color: {heading};
  padding: 4px 0px;
}}
QPlainTextEdit#translucentEditor,
QAbstractScrollArea#translucentEditor {{
  background-color: {canvas_a180};
}}
QTreeView {{
  background-color: {surface};
  color: {fg};
  border: none;
  outline: none;
  padding: 4px;
}}
QTreeView::item {{
  min-height: 22px;
  padding: 3px 6px;
  border-radius: 4px;
}}
QTreeView::item:hover {{
  background-color: {accent_a14};
}}
QTreeView::item:selected {{
  background-color: {accent_a40};
  color: {heading};
}}
QDialog {{
  background-color: {surface};
  color: {fg};
  border: 1px solid {border};
}}
QDialog QLabel,
QMessageBox QLabel {{
  color: {fg};
  background: transparent;
}}
QLineEdit {{
  background-color: {input};
  color: {fg};
  border: 1px solid {border};
  border-radius: 4px;
  padding: 6px 10px;
  min-height: 18px;
  selection-background-color: {accent_a55};
}}
QLineEdit:focus {{
  border: 1px solid {accent};
}}
QPushButton {{
  background-color: {input};
  color: {fg};
  border: 1px solid {border};
  border-radius: 4px;
  padding: 6px 14px;
  min-height: 18px;
}}
QPushButton:hover {{
  background-color: {surface};
  color: {heading};
  border-color: {accent};
}}
QPushButton:default,
QPushButton:pressed {{
  background-color: {accent};
  border-color: {accent};
  color: {on_accent};
  font-weight: 600;
}}
QCheckBox {{
  color: {fg};
  spacing: 8px;
}}
QCheckBox::indicator {{
  width: 14px;
  height: 14px;
  border-radius: 3px;
  border: 1px solid {muted};
  background-color: {canvas};
}}
QCheckBox::indicator:checked {{
  background-color: {accent};
  border-color: {accent};
}}
QSlider::groove:horizontal {{
  height: 4px;
  background: {border};
  border-radius: 2px;
}}
QSlider::handle:horizontal {{
  width: 14px;
  height: 14px;
  margin: -5px 0;
  background: {accent};
  border-radius: 7px;
}}
QSlider::sub-page:horizontal {{
  background: {accent};
  border-radius: 2px;
}}
QGroupBox {{
  border: 1px solid {border};
  border-radius: 6px;
  margin-top: 12px;
  padding: 12px 10px 10px 10px;
  color: {heading};
}}
QGroupBox::title {{
  subcontrol-origin: margin;
  left: 10px;
  padding: 0 6px;
  color: {accent};
}}
QLabel#findDialogStatus {{
  color: {muted};
}}
QListWidget {{
  background-color: {chrome};
  color: {fg};
  border: 1px solid {border};
  border-radius: 4px;
}}
QListWidget::item:selected {{
  background-color: {accent_a40};
  color: {heading};
}}
QComboBox {{
  background-color: {input};
  color: {fg};
  border: 1px solid {border};
  border-radius: 4px;
  padding: 4px 8px;
  min-height: 18px;
}}
QComboBox:focus {{
  border: 1px solid {accent};
}}
QComboBox QAbstractItemView {{
  background-color: {surface};
  color: {fg};
  selection-background-color: {accent_a40};
  border: 1px solid {border};
}}
QSplitter::handle {{
  background-color: {border};
}}
QSplitter::handle:horizontal {{ width: 1px; }}
QSplitter::handle:vertical {{ height: 1px; }}
QScrollBar:vertical {{
  background: {canvas};
  width: 10px;
  border: none;
}}
QScrollBar::handle:vertical {{
  background: {border};
  min-height: 28px;
  border-radius: 4px;
  margin: 2px;
}}
QScrollBar::handle:vertical:hover {{
  background: {muted};
}}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
  height: 0; border: none; background: none;
}}
QScrollBar:horizontal {{
  background: {canvas};
  height: 10px;
  border: none;
}}
QScrollBar::handle:horizontal {{
  background: {border};
  min-width: 28px;
  border-radius: 4px;
  margin: 2px;
}}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {{
  width: 0; border: none; background: none;
}}
QToolTip {{
  background-color: {surface};
  color: {heading};
  border: 1px solid {accent};
  padding: 4px 8px;
  border-radius: 4px;
}}
QMessageBox, QDialog#aboutDialog, QDialog#confirmDialog {{
  background-color: {surface};
  color: {fg};
  border: 1px solid {border};
  border-radius: 8px;
}}
QDialog#aboutDialog QLabel {{
  color: {fg};
  padding: 6px 4px;
}}
QLabel#aboutTitle {{
  color: {heading};
  font-weight: 600;
}}
QLabel#aboutMuted {{
  color: {muted};
}}
QLabel#aboutBody {{
  color: {fg};
}}
QMessageBox QPushButton, QPushButton#aboutOk {{
  min-width: 88px;
  min-height: 28px;
  padding: 6px 16px;
  border-radius: 6px;
  background-color: {input};
  color: {heading};
  border: 1px solid {border};
}}
QMessageBox QPushButton:hover, QPushButton#aboutOk:hover {{
  border-color: {accent};
}}
QMessageBox QPushButton:default, QPushButton#aboutOk {{
  background-color: {accent_a28};
  border: 1px solid {accent};
  color: {heading};
}}
QLabel#confirmText, QLabel#confirmInfo {{
  color: {fg};
  min-width: 280px;
  max-width: 480px;
}}
"""


def render(skin: dict[str, str]) -> str:
    accent = skin["accent"]
    canvas = skin["canvas"]
    ctx = dict(skin)
    ctx.update(
        accent_a14=_rgba(accent, 14),
        accent_a18=_rgba(accent, 18),
        accent_a22=_rgba(accent, 22),
        accent_a28=_rgba(accent, 28),
        accent_a36=_rgba(accent, 36),
        accent_a40=_rgba(accent, 40),
        accent_a50=_rgba(accent, 50),
        accent_a55=_rgba(accent, 55),
        accent_a80=_rgba(accent, 80),
        canvas_a180=_rgba(canvas, 180),
    )
    return TEMPLATE.format(**ctx)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, skin in SKINS.items():
        path = OUT / f"{name}.qss"
        path.write_text(render(skin), encoding="utf-8")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
