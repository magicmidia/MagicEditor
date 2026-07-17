"""Language / extension detection catalog."""

from __future__ import annotations

from magiceditor.core.syntax.detect import detect_language, supported_languages


def test_common_extensions() -> None:
    assert detect_language(None, "app.py") == "python"
    assert detect_language(None, "main.ts") == "typescript"
    assert detect_language(None, "Dockerfile") == "dockerfile"
    assert detect_language(None, "docker-compose.yml") == "yaml"
    assert detect_language(None, "query.sql") == "sql"
    assert detect_language(None, "mod.go") == "go"
    assert detect_language(None, "lib.rs") == "rust"
    assert detect_language(None, "Component.vue") == "vue"
    assert detect_language(None, "token.sol") == "solidity"


def test_supported_menu_languages_nonempty() -> None:
    langs = supported_languages()
    assert len(langs) >= 30
    ids = {i for i, _ in langs}
    assert "python" in ids
    assert "text" in ids
