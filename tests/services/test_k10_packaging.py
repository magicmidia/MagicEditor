"""K10: onedir daily path; onefile skips optional qtawesome/spell datas."""

from pathlib import Path

from magiceditor.services.packaging_measure import measure_packaging, repo_root


def test_measure_packaging_reports_daily_onedir_and_upx_off() -> None:
    """Shipped measure of spec flags (K10: medir onefile/UPX/dicts/onedir)."""
    report = measure_packaging(repo_root())
    assert report["onefile_upx_off"] is True
    assert report["onedir_upx_off"] is True
    assert report["onedir_collect"] is True
    assert report["onefile_lazy_datas"] is True
    assert report["onedir_spell_datas"] is True
    assert report["build_onedir_flag"] is True


def test_onedir_spec_collects_optional_datas() -> None:
    spec = Path("MagicEditor-onedir.spec").read_text(encoding="utf-8")
    assert "COLLECT" in spec
    assert "upx=False" in spec
    assert "collect_data_files" in spec
    assert "spellchecker" in spec


def test_onefile_spec_skips_optional_datas() -> None:
    spec = Path("MagicEditor.spec").read_text(encoding="utf-8")
    assert "collect_data_files" not in spec
    assert "upx=False" in spec


def test_build_ps1_has_onedir_flag() -> None:
    text = Path("scripts/build.ps1").read_text(encoding="utf-8")
    assert "[switch]$Onedir" in text
    assert "MagicEditor-onedir.spec" in text
