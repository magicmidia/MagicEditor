"""Central version module."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from magiceditor.paths import read_changelog
from magiceditor.version import (
    STAGE,
    VERSION,
    about_version_text,
    changelog_contains,
    changelog_section,
    parse_semver,
    pep440,
    release_tag,
    version_display,
    version_label,
)

ROOT = Path(__file__).resolve().parents[1]


def test_version_is_098_beta() -> None:
    assert VERSION == "0.9.8"
    assert STAGE.upper() == "BETA"
    assert version_display() == "0.9.8 BETA"
    assert version_label() == "v0.9.8 BETA"
    assert "0.9.8" in about_version_text()
    assert pep440().startswith("0.9.8")


def test_package_dunder_version() -> None:
    import magiceditor

    assert magiceditor.__version__ == "0.9.8"


def test_semver_parse_and_release_tag() -> None:
    parsed = parse_semver("0.9.8")
    assert (parsed.major, parsed.minor, parsed.patch) == (0, 9, 8)
    assert parsed.prerelease == ""
    assert str(parsed) == "0.9.8"
    pre = parse_semver("1.0.0-beta.1")
    assert pre.prerelease == "beta.1"
    assert str(pre) == "1.0.0-beta.1"
    built = parse_semver("1.2.3+build.7")
    assert built.build == "build.7"
    with pytest.raises(ValueError):
        parse_semver("0.9")
    with pytest.raises(ValueError):
        parse_semver("v0.9.8")
    assert release_tag() == f"v{VERSION}"
    assert release_tag("1.0.0-beta.1") == "v1.0.0-beta.1"


def test_changelog_section_matches_version() -> None:
    text = read_changelog()
    assert changelog_contains(text, VERSION)
    section = changelog_section(text, VERSION)
    assert section.startswith(f"## [{VERSION}]")
    assert "## [0.9.7]" not in section
    assert changelog_section(text, "9.9.9") == ""


def _load_script(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_release_sources_agree() -> None:
    checker = _load_script("check_release_version.py")
    assert checker.problems(ROOT) == []
    assert checker.problems(ROOT, tag=release_tag()) == []
    mismatch = checker.problems(ROOT, tag="v0.0.1")
    assert len(mismatch) == 1
    assert "v0.0.1" in mismatch[0]
    assert checker.project_version('[project]\nversion = "0.9.8"\n') == "0.9.8"
    assert checker.inno_version('  #define MyAppVersion "0.9.8"\n') == "0.9.8"


def test_check_release_script_cli() -> None:
    script = ROOT / "scripts" / "check_release_version.py"
    ok = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert ok.returncode == 0, ok.stderr
    assert "semver OK" in ok.stdout
    bad = subprocess.run(
        [sys.executable, str(script), "--tag", "v0.0.1"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert bad.returncode == 1
    assert "v0.0.1" in bad.stderr


def test_changelog_notes_writes_current_section(tmp_path: Path) -> None:
    notes = _load_script("changelog_notes.py")
    out = tmp_path / "notes.md"
    assert notes.main(["--out", str(out)]) == 0
    body = out.read_text(encoding="utf-8")
    assert body.startswith(f"## [{VERSION}]")
    assert "## [0.9.7]" not in body


def test_bump_inserts_heading_only_in_copy(tmp_path: Path) -> None:
    bump = _load_script("bump_version.py")
    docs = tmp_path / "docs"
    docs.mkdir()
    changelog = docs / "CHANGELOG.md"
    changelog.write_text(
        "# Changelog\n\n## [Unreleased]\n\n## [0.9.8] — shipped\n\n- item\n",
        encoding="utf-8",
    )
    bump.ROOT = tmp_path
    bump._ensure_changelog_heading("0.9.9")
    text = changelog.read_text(encoding="utf-8")
    assert text.index("## [Unreleased]") < text.index("## [0.9.9]") < text.index("## [0.9.8]")
    bump._ensure_changelog_heading("0.9.9")
    assert changelog.read_text(encoding="utf-8").count("## [0.9.9]") == 1
