"""Encode/decode single-instance open messages (no Qt)."""

from __future__ import annotations

PREFIX = "MEOPEN\n"


def encode_open(paths: list[str]) -> bytes:
    cleaned = [p.strip() for p in paths if p and str(p).strip()]
    return (PREFIX + "\n".join(cleaned) + "\n").encode("utf-8")


def decode_open(data: bytes) -> list[str]:
    text = (data or b"").decode("utf-8", errors="replace")
    if not text.startswith(PREFIX):
        return []
    out: list[str] = []
    for line in text[len(PREFIX) :].splitlines():
        item = line.strip()
        if item:
            out.append(item)
    return out
