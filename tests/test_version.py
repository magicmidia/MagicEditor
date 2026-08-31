"""Central version module."""

from magiceditor.version import (
    STAGE,
    VERSION,
    about_version_text,
    pep440,
    version_display,
    version_label,
)


def test_version_is_094_beta() -> None:
    assert VERSION == "0.9.4"
    assert STAGE.upper() == "BETA"
    assert version_display() == "0.9.4 BETA"
    assert version_label() == "v0.9.4 BETA"
    assert "0.9.4" in about_version_text()
    assert pep440().startswith("0.9.4")


def test_package_dunder_version() -> None:
    import magiceditor

    assert magiceditor.__version__ == "0.9.4"
