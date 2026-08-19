"""Settings dialog pages — one module per pane (J1.4)."""

from magiceditor.ui.settings_pages.design import DesignPage
from magiceditor.ui.settings_pages.editor import EditorPage
from magiceditor.ui.settings_pages.general import GeneralPage
from magiceditor.ui.settings_pages.graphics import GraphicsPage
from magiceditor.ui.settings_pages.performance import PerformancePage
from magiceditor.ui.settings_pages.spell import SpellPage
from magiceditor.ui.settings_pages.tabs import TabsPage

__all__ = [
    "DesignPage",
    "EditorPage",
    "GeneralPage",
    "GraphicsPage",
    "PerformancePage",
    "SpellPage",
    "TabsPage",
]
