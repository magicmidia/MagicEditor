"""K11: global QWidget must not force transparent polish on every widget."""

from pathlib import Path


def test_qss_qwidget_has_no_transparent_background() -> None:
    root = Path("resources/themes")
    for qss in root.glob("*.qss"):
        text = qss.read_text(encoding="utf-8")
        idx = 0
        while True:
            start = text.find("QWidget {", idx)
            if start < 0:
                break
            end = text.find("}", start)
            block = text[start:end]
            assert "background-color: transparent" not in block, qss.name
            assert "background: transparent" not in block, qss.name
            idx = end + 1
