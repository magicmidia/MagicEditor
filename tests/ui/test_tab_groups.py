"""Tab groups + scroll chrome (offscreen)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path
from unittest.mock import Mock

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication, QLabel

from magiceditor.services.session_state import SessionState
from magiceditor.services.settings import AppSettings
from magiceditor.ui.tab_groups import GROUP_COLORS, TabGroup
from magiceditor.ui.tab_manager import TabManager
from magiceditor.ui.window_session import collect_tab_groups, plan_group_restore


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_create_group_and_color(qapp) -> None:
    tabs = TabManager()
    a = QLabel("a")
    b = QLabel("b")
    c = QLabel("c")
    tabs.addTab(a, "a.txt")
    tabs.addTab(b, "b.txt")
    tabs.addTab(c, "c.txt")
    g = tabs.create_group([0, 1], name="Work", color=GROUP_COLORS[0][1])
    assert g is not None
    assert g.name == "Work"
    assert tabs.group_of_index(0) is g
    assert tabs.group_of_index(1) is g
    assert tabs.group_of_index(2) is None
    tabs.remove_from_group(1)
    assert tabs.group_of_index(1) is None
    assert tabs.group_of_index(0) is g


def test_collapse_group_hides_members(qapp) -> None:
    tabs = TabManager()
    for name in ("x", "y", "z"):
        tabs.addTab(QLabel(name), name)
    g = tabs.create_group([0, 1, 2], name="Pack")
    assert g is not None
    tabs.set_group_collapsed(g.group_id, True)
    bar = tabs.tabBar()
    visible = [i for i in range(tabs.count()) if bar.isTabVisible(i)]
    assert len(visible) == 1
    tabs.set_group_collapsed(g.group_id, False)
    visible = [i for i in range(tabs.count()) if bar.isTabVisible(i)]
    assert len(visible) == 3


def test_scroll_buttons_exist(qapp) -> None:
    tabs = TabManager()
    assert tabs._scroll_left is not None
    assert tabs._scroll_right is not None
    tabs.addTab(QLabel("1"), "1")
    tabs.addTab(QLabel("2"), "2")
    tabs._update_scroll_buttons()
    # Not shown without a parent window; still enabled for multi-tab nav.
    assert tabs._scroll_right.isEnabled()


def test_groups_changed_fires_connected_handler(qapp) -> None:
    tabs = TabManager()
    for name in ("a", "b", "c"):
        tabs.addTab(QLabel(name), name)
    g = tabs.create_group([0], name="Work")
    assert g is not None
    handler = Mock()
    tabs.groups_changed.connect(handler)
    tabs.add_to_group(1, g.group_id)
    handler.assert_called()
    handler.reset_mock()
    tabs.remove_from_group(1)
    handler.assert_called()


def test_collect_and_plan_group_restore_roundtrip(qapp) -> None:
    tabs = TabManager()
    widgets = [QLabel(n) for n in ("a", "b", "c")]
    for i, w in enumerate(widgets):
        tabs.addTab(w, f"{i}.txt")
    g = tabs.create_group([0, 2], name="Pack", color=GROUP_COLORS[1][1])
    assert g is not None
    tabs.set_group_collapsed(g.group_id, True)

    keys = {
        id(widgets[0]): "/tmp/a.txt",
        id(widgets[1]): "/tmp/b.txt",
        id(widgets[2]): "Untitled-1",
    }
    data = collect_tab_groups(tabs.list_groups(), keys)
    assert data == [
        {
            "name": "Pack",
            "color": GROUP_COLORS[1][1],
            "collapsed": True,
            "members": ["/tmp/a.txt", "Untitled-1"],
        }
    ]

    available = ["/tmp/a.txt", "/tmp/b.txt", "Untitled-1"]
    ops = plan_group_restore(data, available)
    assert len(ops) == 1
    op = ops[0]
    assert op.name == "Pack"
    assert op.color == GROUP_COLORS[1][1]
    assert op.collapsed is True
    assert op.member_indices == [0, 2]


def test_plan_group_restore_ignores_missing_members(qapp) -> None:
    data = [
        {"name": "Gone", "color": "#fff", "collapsed": False, "members": ["nope"]},
        {"name": "Partial", "color": "", "collapsed": False, "members": ["nope", "hit"]},
        {"name": "", "color": "#fff", "collapsed": False, "members": ["hit"]},
        "not-a-dict",
    ]
    ops = plan_group_restore(data, ["hit"])  # type: ignore[list-item]
    assert len(ops) == 1
    assert ops[0].name == "Partial"
    assert ops[0].member_indices == [0]
    assert ops[0].color is None


def test_tab_groups_settings_roundtrip(tmp_path: Path) -> None:
    qs = QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat)
    s = AppSettings(settings=qs)
    groups = [
        {
            "name": "Work",
            "color": "#3B82F6",
            "collapsed": True,
            "members": ["a.txt", "Untitled-1"],
        }
    ]
    s.save(SessionState(tab_groups=groups))
    loaded = s.load()
    assert loaded.tab_groups == groups


def test_tab_groups_settings_tolerant_load(tmp_path: Path) -> None:
    qs = QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat)
    qs.setValue("session/tab_groups_json", "{not json")
    s = AppSettings(settings=qs)
    assert s.load().tab_groups == []
    qs.setValue(
        "session/tab_groups_json",
        '[{"name":"","members":["x"]},{"name":"Ok","members":"nope"},42]',
    )
    loaded = s.load()
    assert loaded.tab_groups == [{"name": "Ok", "color": "", "collapsed": False, "members": []}]


def test_collect_tab_groups_drops_empty(qapp) -> None:
    orphan = TabGroup(group_id="x1", name="Orphan", color="#fff", members=[999999])
    assert collect_tab_groups([orphan], {}) == []
