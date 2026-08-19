from magiceditor.services.instance_protocol import decode_open, encode_open


def test_encode_decode_roundtrip() -> None:
    raw = encode_open([r"C:\docs\a.txt", "  ", r"D:\b.md"])
    assert decode_open(raw) == [r"C:\docs\a.txt", r"D:\b.md"]


def test_decode_rejects_unknown() -> None:
    assert decode_open(b"hello") == []
    assert decode_open(b"") == []
