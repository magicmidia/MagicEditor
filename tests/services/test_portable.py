from pathlib import Path

from magiceditor.services.portable import is_portable_mode, portable_config_dir


def test_portable_ini(tmp_path: Path) -> None:
    assert is_portable_mode(tmp_path) is False
    (tmp_path / "portable.ini").write_text("[portable]\n", encoding="utf-8")
    assert is_portable_mode(tmp_path) is True
    cfg = portable_config_dir(tmp_path)
    assert cfg is not None
    assert cfg.is_dir()
