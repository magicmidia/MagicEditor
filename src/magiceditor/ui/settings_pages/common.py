"""Shared settings-page chrome (J1.4)."""

from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QLabel, QScrollArea, QWidget

Translate = Callable[[str, str], str]


def wrap_scroll(parent: QWidget, inner: QWidget) -> QWidget:
    scroll = QScrollArea(parent)
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setWidget(inner)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    return scroll


def hint_label(text: str, parent: QWidget) -> QLabel:
    tip = QLabel(text, parent)
    tip.setWordWrap(True)
    tip.setObjectName("findDialogStatus")
    return tip
