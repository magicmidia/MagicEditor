"""Regression: session restore used to call watch_path before the watcher existed."""

from magiceditor.ui.power_features import PowerFeaturesMixin


def test_watch_path_without_watcher_is_noop() -> None:
    class Host:
        pass

    PowerFeaturesMixin.watch_path(Host(), None)
    PowerFeaturesMixin.watch_path(Host(), "C:\\missing.txt")
