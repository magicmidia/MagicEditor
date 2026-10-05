"""Micro-animations for tab groups.

Pattern (project standard — first animations in the codebase):

- ``QVariantAnimation``, 120-180 ms, ``QEasingCurve.Type.OutCubic``.
- ``valueChanged`` mutates paint state on the bar (``_drop_highlight_alpha``
  / ``_stripe_pulses``) and calls ``bar.update()``; painting stays in
  ``MagicTabBar.paintEvent``.
- Animations are parented to the bar AND tracked by ``TabGroupAnimator``
  (which owns the strong refs) so the GC cannot kill them mid-flight.
- Works headless: ``QVariantAnimation`` needs no display; in tests either
  shorten the duration, drive ``setCurrentTime``/``stop()``, or wait out the
  <200 ms run with ``QTest.qWait``.
"""

from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QObject, QVariantAnimation

from magiceditor.ui.magic_tab_bar import MagicTabBar

_PULSE_MS = 160
_FADE_MS = 140


def fade_drop_highlight(bar: MagicTabBar) -> QVariantAnimation:
    """Fade the drop-highlight alpha 160→0, then clear the highlight."""
    anim = QVariantAnimation(bar)
    anim.setDuration(_FADE_MS)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.setStartValue(160)
    anim.setEndValue(0)

    def _apply(value: object) -> None:
        bar._drop_highlight_alpha = int(value)  # type: ignore[arg-type]
        bar.update()

    anim.valueChanged.connect(_apply)
    anim.finished.connect(bar.clear_drop_highlight)
    anim.start()
    return anim


def pulse_stripe(bar: MagicTabBar, index: int, color: str) -> QVariantAnimation:
    """Pulse the group stripe of tab ``index`` (alpha 0→220→140).

    The pulse overrides the stripe alpha via ``bar._stripe_pulses[index]``;
    on finish the override is removed so the stripe returns to full color.
    ``color`` is accepted for caller clarity; the painted color always comes
    from the group mapping.
    """
    del color  # stripe color comes from the group mapping at paint time
    anim = QVariantAnimation(bar)
    anim.setDuration(_PULSE_MS)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.setStartValue(0)
    anim.setKeyValueAt(0.5, 220)
    anim.setEndValue(140)

    def _apply(value: object) -> None:
        bar._stripe_pulses[index] = int(value)  # type: ignore[arg-type]
        bar.update()

    def _done() -> None:
        bar._stripe_pulses.pop(index, None)
        bar.update()

    anim.valueChanged.connect(_apply)
    anim.finished.connect(_done)
    anim.start()
    return anim


class TabGroupAnimator(QObject):
    """Owns active group animations keyed by (bar, index); GC-safe."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._active: dict[tuple[int, int], QVariantAnimation] = {}

    def _track(self, key: tuple[int, int], anim: QVariantAnimation) -> None:
        self._active[key] = anim
        anim.finished.connect(lambda k=key: self._active.pop(k, None))

    def _stop(self, key: tuple[int, int]) -> None:
        anim = self._active.pop(key, None)
        if anim is not None:
            anim.stop()

    def pulse(self, bar: MagicTabBar, index: int, color: str) -> QVariantAnimation | None:
        """Stripe pulse on group join; ignored for invalid indices."""
        if not 0 <= index < bar.count():
            return None
        key = (id(bar), index)
        self._stop(key)
        anim = pulse_stripe(bar, index, color)
        self._track(key, anim)
        return anim

    def fade_highlight(self, bar: MagicTabBar) -> QVariantAnimation:
        """Fade the drop highlight out (key ``(bar, -1)``)."""
        key = (id(bar), -1)
        self._stop(key)
        anim = fade_drop_highlight(bar)
        self._track(key, anim)
        return anim

    def stop_index(self, bar: MagicTabBar, index: int) -> None:
        """Stop any pulse running for ``index`` (e.g. tab left the group)."""
        self._stop((id(bar), index))

    def stop_all(self) -> None:
        for anim in self._active.values():
            anim.stop()
        self._active.clear()
