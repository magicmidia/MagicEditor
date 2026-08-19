from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]


def test_pyproject_has_coverage_fail_under() -> None:
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert "fail_under" in text
    assert "70" in text


def test_per_package_fail_under_core_higher_than_ui() -> None:
    data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    floors = data["tool"]["magiceditor"]["coverage"]
    assert floors["fail_under_core"] >= 80
    assert floors["fail_under_ui"] >= 30
    assert floors["fail_under_core"] > floors["fail_under_ui"]
    assert floors["fail_under_services"] >= 50
