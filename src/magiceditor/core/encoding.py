"""Encoding and end-of-line detection helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Eol = Literal["LF", "CRLF", "CR", "MIXED", "NONE"]
EncodingName = Literal["utf-8", "utf-8-sig", "latin-1", "cp1252"]


@dataclass(slots=True, frozen=True)
class TextProbe:
    encoding: EncodingName
    eol: Eol
    text: str
    raw: bytes


def detect_eol(data: bytes) -> Eol:
    has_crlf = b"\r\n" in data
    # Count bare CR / LF excluding CRLF pairs roughly
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
    if has_crlf and not has_lf and not has_cr:
        return "CRLF"
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


def decode_bytes(data: bytes) -> TextProbe:
    """Decode with a small priority list suitable for editor files."""
    candidates: list[EncodingName] = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]
    last_error: Exception | None = None
    for enc in candidates:
        try:
            if enc == "latin-1":
                text = data.decode("latin-1")
            else:
                text = data.decode(enc)
            # Prefer utf-8 when it works without replacement issues
            return TextProbe(
                encoding=enc if enc != "utf-8-sig" else "utf-8-sig",
                eol=detect_eol(data),
                text=text,
                raw=data,
            )
        except UnicodeDecodeError as exc:
            last_error = exc
            continue
    # latin-1 always succeeds; this is unreachable but keeps type-checkers happy
    if last_error:
        text = data.decode("latin-1")
        return TextProbe(encoding="latin-1", eol=detect_eol(data), text=text, raw=data)
    text = data.decode("latin-1")
    return TextProbe(encoding="latin-1", eol=detect_eol(data), text=text, raw=data)
