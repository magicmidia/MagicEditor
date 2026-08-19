import pytest

from magiceditor.i18n.translator import TranslatorManager


def test_translator_rejects_path_escape(tmp_path) -> None:
    tr = TranslatorManager(locales_path=tmp_path)
    with pytest.raises(ValueError):
        tr.load("../en_US")
    with pytest.raises(ValueError):
        tr.load("foo/bar")
