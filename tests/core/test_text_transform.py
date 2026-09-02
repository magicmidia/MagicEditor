"""Tests for pure text transformation functions."""

import pytest

from magiceditor.core.text_transform import (
    base64_decode,
    base64_encode,
    invert_case,
    to_lower,
    to_sentence_case,
    to_title_case,
    to_upper,
    url_decode,
    url_encode,
)


def test_to_upper_with_accents() -> None:
    assert to_upper("ação não é açúcar") == "AÇÃO NÃO É AÇÚCAR"


def test_to_lower_with_accents() -> None:
    assert to_lower("AÇÃO NÃO É AÇÚCAR") == "ação não é açúcar"


def test_to_title_case_with_accents() -> None:
    assert to_title_case("ação não é açúcar") == "Ação Não É Açúcar"


def test_to_title_case_preserves_apostrophes() -> None:
    # str.title() would produce "Don'T"; word-wise capitalize must not
    assert to_title_case("don't stop") == "Don't Stop"


def test_to_title_case_lowercases_rest() -> None:
    assert to_title_case("hELLO wORLD") == "Hello World"


def test_to_sentence_case() -> None:
    assert to_sentence_case("ação não é açúcar. ISSO É BOM! ok? SIM") == (
        "Ação não é açúcar. Isso é bom! Ok? Sim"
    )


def test_to_sentence_case_no_terminal_punctuation() -> None:
    assert to_sentence_case("OLÁ MUNDO") == "Olá mundo"


def test_invert_case_with_accents() -> None:
    assert invert_case("Ação NÃO") == "aÇÃO não"


def test_case_functions_empty_and_plain() -> None:
    assert to_upper("") == ""
    assert to_lower("") == ""
    assert to_title_case("") == ""
    assert to_sentence_case("") == ""
    assert invert_case("") == ""
    # no newline in selection, no transformation needed -> idempotent
    assert to_upper("ABC") == "ABC"
    assert to_lower("abc") == "abc"


def test_base64_roundtrip_with_accents() -> None:
    original = "ação não é açúcar"
    encoded = base64_encode(original)
    assert encoded.isascii()
    assert base64_decode(encoded) == original


def test_base64_encode_known_value() -> None:
    assert base64_encode("hello") == "aGVsbG8="
    assert base64_decode("aGVsbG8=") == "hello"


def test_base64_decode_invalid_raises_value_error() -> None:
    with pytest.raises(ValueError, match="base64"):
        base64_decode("!!!not-base64!!!")


def test_base64_empty() -> None:
    assert base64_encode("") == ""
    assert base64_decode("") == ""


def test_url_roundtrip_percent_and_plus() -> None:
    original = "ação não é açúcar"
    encoded = url_encode(original)
    assert "%" in encoded and " " not in encoded
    assert url_decode(encoded) == original


def test_url_decode_plus_as_space() -> None:
    assert url_decode("ola+mundo%20%C3%A9") == "ola mundo é"


def test_url_encode_reserved_chars() -> None:
    encoded = url_encode("a b&c=d")
    assert " " not in encoded and "&" not in encoded and "=" not in encoded
    assert url_decode(encoded) == "a b&c=d"


def test_url_empty() -> None:
    assert url_encode("") == ""
    assert url_decode("") == ""
