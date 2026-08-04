"""Chrome-style tab groups (metadata + collapse helpers)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

GROUP_COLORS: tuple[tuple[str, str], ...] = (
    ("blue", "#3B82F6"),
    ("green", "#22C55E"),
    ("yellow", "#EAB308"),
    ("orange", "#F97316"),
    ("red", "#EF4444"),
    ("purple", "#A855F7"),
    ("cyan", "#06B6D4"),
    ("pink", "#EC4899"),
)


@dataclass
class TabGroup:
    group_id: str
    name: str
    color: str  # hex
    collapsed: bool = False
    members: list[int] = field(default_factory=list)  # id(widget)


class TabGroupStore:
    """Owns group membership keyed by widget identity."""

    def __init__(self) -> None:
        self.groups: dict[str, TabGroup] = {}
        self.widget_group: dict[int, str] = {}

    def group_of_widget(self, widget_id: int) -> TabGroup | None:
        gid = self.widget_group.get(widget_id)
        return self.groups.get(gid) if gid else None

    def create(
        self,
        widget_ids: list[int],
        *,
        name: str | None = None,
        color: str | None = None,
    ) -> TabGroup | None:
        if not widget_ids:
            return None
        gid = uuid.uuid4().hex[:8]
        color = color or GROUP_COLORS[len(self.groups) % len(GROUP_COLORS)][1]
        name = name or f"Grupo {len(self.groups) + 1}"
        group = TabGroup(group_id=gid, name=name, color=color)
        for wid in widget_ids:
            self._detach(wid)
            self.widget_group[wid] = gid
            group.members.append(wid)
        self.groups[gid] = group
        return group

    def add(self, widget_id: int, group_id: str) -> None:
        group = self.groups.get(group_id)
        if group is None:
            return
        self._detach(widget_id)
        self.widget_group[widget_id] = group_id
        if widget_id not in group.members:
            group.members.append(widget_id)

    def remove(self, widget_id: int) -> None:
        self._detach(widget_id)

    def rename(self, group_id: str, name: str) -> None:
        g = self.groups.get(group_id)
        if g and name.strip():
            g.name = name.strip()

    def set_color(self, group_id: str, color: str) -> None:
        g = self.groups.get(group_id)
        if g:
            g.color = color

    def set_collapsed(self, group_id: str, collapsed: bool) -> TabGroup | None:
        g = self.groups.get(group_id)
        if g is None:
            return None
        g.collapsed = collapsed
        return g

    def prune(self, live_ids: set[int]) -> None:
        self.widget_group = {k: v for k, v in self.widget_group.items() if k in live_ids}
        dead: list[str] = []
        for gid, g in self.groups.items():
            g.members = [m for m in g.members if m in live_ids]
            if not g.members:
                dead.append(gid)
        for gid in dead:
            del self.groups[gid]

    def color_map_for_indices(self, index_to_widget_id: dict[int, int]) -> dict[int, str]:
        mapping: dict[int, str] = {}
        for idx, wid in index_to_widget_id.items():
            g = self.group_of_widget(wid)
            if g is not None:
                mapping[idx] = g.color
        return mapping

    def _detach(self, widget_id: int) -> None:
        old = self.widget_group.pop(widget_id, None)
        if not old or old not in self.groups:
            return
        g = self.groups[old]
        g.members = [m for m in g.members if m != widget_id]
        if not g.members:
            del self.groups[old]
