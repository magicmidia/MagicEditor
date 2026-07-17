"""Encoding and end-of-line detection / conversion helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Eol = Literal["LF", "CRLF", "CR", "MIXED", "NONE"]
# Codec names accepted by Python's codecs registry
EncodingName = str

# (codec, display label) — broad set for Format → Encoding menu
ENCODING_CATALOG: list[tuple[str, str]] = [
    ("utf-8", "UTF-8"),
    ("utf-8-sig", "UTF-8 with BOM"),
    ("utf-16", "UTF-16"),
    ("utf-16-le", "UTF-16 LE"),
    ("utf-16-be", "UTF-16 BE"),
    ("utf-32", "UTF-32"),
    ("utf-32-le", "UTF-32 LE"),
    ("utf-32-be", "UTF-32 BE"),
    ("ascii", "ASCII"),
    ("latin-1", "ISO-8859-1 (Latin-1)"),
    ("iso-8859-2", "ISO-8859-2 (Central Europe)"),
    ("iso-8859-3", "ISO-8859-3 (South Europe)"),
    ("iso-8859-4", "ISO-8859-4 (North Europe)"),
    ("iso-8859-5", "ISO-8859-5 (Cyrillic)"),
    ("iso-8859-6", "ISO-8859-6 (Arabic)"),
    ("iso-8859-7", "ISO-8859-7 (Greek)"),
    ("iso-8859-8", "ISO-8859-8 (Hebrew)"),
    ("iso-8859-9", "ISO-8859-9 (Turkish)"),
    ("iso-8859-10", "ISO-8859-10 (Nordic)"),
    ("iso-8859-13", "ISO-8859-13 (Baltic)"),
    ("iso-8859-14", "ISO-8859-14 (Celtic)"),
    ("iso-8859-15", "ISO-8859-15 (Latin-9)"),
    ("iso-8859-16", "ISO-8859-16 (Romanian)"),
    ("cp037", "IBM EBCDIC (US/Canada)"),
    ("cp437", "CP437 (DOS US)"),
    ("cp850", "CP850 (DOS Latin-1)"),
    ("cp852", "CP852 (DOS Central Europe)"),
    ("cp855", "CP855 (DOS Cyrillic)"),
    ("cp857", "CP857 (DOS Turkish)"),
    ("cp860", "CP860 (DOS Portuguese)"),
    ("cp861", "CP861 (DOS Icelandic)"),
    ("cp862", "CP862 (DOS Hebrew)"),
    ("cp863", "CP863 (DOS French Canada)"),
    ("cp865", "CP865 (DOS Nordic)"),
    ("cp866", "CP866 (DOS Cyrillic Russian)"),
    ("cp869", "CP869 (DOS Greek)"),
    ("cp874", "Windows-874 (Thai)"),
    ("cp932", "Windows-932 / Shift_JIS"),
    ("cp936", "Windows-936 / GBK"),
    ("cp949", "Windows-949 (Korean)"),
    ("cp950", "Windows-950 / Big5"),
    ("cp1250", "Windows-1250 (Central Europe)"),
    ("cp1251", "Windows-1251 (Cyrillic)"),
    ("cp1252", "Windows-1252 (Western)"),
    ("cp1253", "Windows-1253 (Greek)"),
    ("cp1254", "Windows-1254 (Turkish)"),
    ("cp1255", "Windows-1255 (Hebrew)"),
    ("cp1256", "Windows-1256 (Arabic)"),
    ("cp1257", "Windows-1257 (Baltic)"),
    ("cp1258", "Windows-1258 (Vietnamese)"),
    ("koi8-r", "KOI8-R (Russian)"),
    ("koi8-u", "KOI8-U (Ukrainian)"),
    ("mac-roman", "Mac OS Roman"),
    ("mac-cyrillic", "Mac OS Cyrillic"),
    ("mac-greek", "Mac OS Greek"),
    ("mac-turkish", "Mac OS Turkish"),
    ("shift_jis", "Shift_JIS (Japanese)"),
    ("euc-jp", "EUC-JP (Japanese)"),
    ("iso2022-jp", "ISO-2022-JP (Japanese)"),
    ("euc-kr", "EUC-KR (Korean)"),
    ("gbk", "GBK (Simplified Chinese)"),
    ("gb2312", "GB2312 (Simplified Chinese)"),
    ("gb18030", "GB18030 (Chinese)"),
    ("big5", "Big5 (Traditional Chinese)"),
    ("big5hkscs", "Big5-HKSCS"),
    ("hz", "HZ (Chinese)"),
]


@dataclass(slots=True, frozen=True)
class TextProbe:
    encoding: EncodingName
    eol: Eol
    text: str
    raw: bytes


def encoding_label(codec: str) -> str:
    for code, label in ENCODING_CATALOG:
        if code == codec:
            return label
    return codec


def detect_eol(data: bytes) -> Eol:
    has_crlf = b"\r\n" in data
    stripped = data.replace(b"\r\n", b"")
    has_lf = b"\n" in stripped
    has_cr = b"\r" in stripped
    if has_crlf and not has_lf and not has_cr:
        return "CRLF"
    if has_lf and not has_cr and not has_crlf:
        return "LF"
    if has_cr and not has_lf and not has_crlf:
        return "CR"
    if not has_crlf and not has_lf and not has_cr:
        return "NONE"
    kinds = sum([has_crlf, has_lf, has_cr])
    if kinds > 1:
        return "MIXED"
    if has_crlf:
        return "CRLF"
    if has_lf:
        return "LF"
    if has_cr:
        return "CR"
    return "NONE"


def normalize_newlines(data: bytes, target: Eol) -> bytes:
    """Convert line endings in *data* to *target* (LF / CRLF / CR)."""
    if target in {"MIXED", "NONE"}:
        return data
    out = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    if target == "LF":
        return out
    if target == "CRLF":
        return out.replace(b"\n", b"\r\n")
    if target == "CR":
        return out.replace(b"\n", b"\r")
    return data


def _bom_encoding(data: bytes) -> EncodingName | None:
    if data.startswith(b"\xff\xfe\x00\x00"):
        return "utf-32-le"
    if data.startswith(b"\x00\x00\xfe\xff"):
        return "utf-32-be"
    if data.startswith(b"\xff\xfe"):
        return "utf-16-le"
    if data.startswith(b"\xfe\xff"):
        return "utf-16-be"
    if data.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    return None


def _try_decode(data: bytes, enc: str) -> str | None:
    try:
        return data.decode(enc)
    except (UnicodeDecodeError, LookupError, ValueError):
        return None


def decode_bytes(data: bytes) -> TextProbe:
    """Decode with BOM-first then a broad candidate list."""
    eol = detect_eol(data)
    bom = _bom_encoding(data)
    if bom:
        text = _try_decode(data, bom)
        if text is not None:
            return TextProbe(encoding=bom, eol=eol, text=text, raw=data)

    # Prefer UTF-8 when valid; then Western European; then regional codecs
    candidates: list[str] = [
        "utf-8",
        "cp1252",
        "latin-1",
        "cp1250",
        "cp1251",
        "cp850",
        "cp437",
        "shift_jis",
        "cp932",
        "gbk",
        "gb18030",
        "big5",
        "euc-kr",
        "euc-jp",
        "koi8-r",
        "iso-8859-2",
        "iso-8859-15",
        "utf-16",
        "utf-16-le",
        "utf-16-be",
        "mac-roman",
    ]
    for enc in candidates:
        text = _try_decode(data, enc)
        if text is None:
            continue
        # Reject UTF-16/32 guesses that produce many NULs for short ASCII-like files
        if enc.startswith("utf-16") or enc.startswith("utf-32"):
            if data and data.count(0) > max(2, len(data) // 4):
                # ok for real UTF-16
                pass
            elif b"\x00" not in data[: min(64, len(data))] and enc != "utf-8":
                continue
        return TextProbe(encoding=enc, eol=eol, text=text, raw=data)

    # latin-1 always succeeds
    text = data.decode("latin-1")
    return TextProbe(encoding="latin-1", eol=eol, text=text, raw=data)


def encode_text(text: str, encoding: EncodingName) -> bytes:
    """Encode *text* for disk, adding BOM when required by codec name."""
    enc = encoding or "utf-8"
    try:
        data = text.encode(enc, errors="replace")
    except LookupError:
        data = text.encode("utf-8", errors="replace")
        enc = "utf-8"
    # Explicit BOM for utf-8-sig is handled by the codec; for others, trust codec.
    if enc == "utf-8-sig" and not data.startswith(b"\xef\xbb\xbf"):
        data = b"\xef\xbb\xbf" + data
    return data
