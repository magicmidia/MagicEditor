import json
from pathlib import Path

from magiceditor.services.file_associations import DEFAULT_EXTENSIONS


def test_wix_json_matches_default_extensions() -> None:
    raw = Path("packaging/wix/file-associations.json").read_text(encoding="utf-8")
    data = json.loads(raw)
    assert ".env" in data["extensions"]
    assert ".gitignore" in data["extensions"]
    assert ".bat" not in data["extensions"]
    assert ".cmd" not in data["extensions"]
    assert set(data["extensions"]) == set(DEFAULT_EXTENSIONS)
    from magiceditor.services.file_associations import NATIVE_SCRIPT_PROGIDS

    assert NATIVE_SCRIPT_PROGIDS[".bat"] == "batfile"
    assert NATIVE_SCRIPT_PROGIDS[".cmd"] == "cmdfile"
    iss = Path("packaging/inno/MagicEditor.iss").read_text(encoding="utf-8")
    assert 'ValueData: "batfile"' in iss
    assert 'ValueData: "cmdfile"' in iss
    assert "RestoreNativeScriptHandlers" in iss
    assert r"FileExts\.bat\OpenWithProgids" in iss
    assert r"FileExts\.cmd\OpenWithList" in iss
