from pathlib import Path

from magiceditor.services.file_associations import (
    DEFAULT_EXTENSIONS,
    association_extensions,
    association_manifest,
    write_manifest,
)


def test_extensions_include_text_types() -> None:
    ext = association_extensions()
    assert ".txt" in ext
    assert ".md" in ext
    assert ".py" in ext
    assert len(ext) == len(DEFAULT_EXTENSIONS)


def test_manifest_write(tmp_path: Path) -> None:
    path = write_manifest(tmp_path / "file-associations.json")
    data = association_manifest()
    assert path.is_file()
    assert data["progid"] == "MagicEditor.Document"
    text = path.read_text(encoding="utf-8")
    assert ".txt" in text
