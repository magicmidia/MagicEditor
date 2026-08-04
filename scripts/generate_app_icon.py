#!/usr/bin/env python3
"""Generate resources/icons/app/magiceditor.ico (multi-size monogram M).

Run from repo root:
  python scripts/generate_app_icon.py
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_ICO = ROOT / "resources" / "icons" / "app" / "magiceditor.ico"
OUT_PNG = ROOT / "resources" / "icons" / "app" / "magiceditor-256.png"
SIZES = (16, 24, 32, 48, 64, 128, 256)


def _png_rgba(w: int, h: int, pixels: list[tuple[int, int, int, int]]) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            r, g, b, a = pixels[y * w + x]
            raw.extend((r, g, b, a))
    return b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)),
            chunk(b"IDAT", zlib.compress(bytes(raw), 9)),
            chunk(b"IEND", b""),
        ]
    )


def _monogram(size: int) -> list[tuple[int, int, int, int]]:
    """Luminous Void monogram: dark canvas + gold M."""
    bg = (14, 14, 14, 255)
    gold = (255, 215, 0, 255)
    px = [bg] * (size * size)

    def setp(x: int, y: int, c: tuple[int, int, int, int]) -> None:
        if 0 <= x < size and 0 <= y < size:
            px[y * size + x] = c

    rad = max(2, int(size * 0.22))
    for y in range(size):
        for x in range(size):
            cx = min(max(x, rad), size - 1 - rad)
            cy = min(max(y, rad), size - 1 - rad)
            dx, dy = x - cx, y - cy
            if dx * dx + dy * dy <= rad * rad + rad * 0.5:
                surface = (20, 19, 18, 255)
                if dx * dx + dy * dy > (rad - 1) ** 2:
                    surface = (28, 26, 20, 255)
                setp(x, y, surface)

    m = size * 0.20
    pts = [
        (m, size - m),
        (m, m * 1.15),
        (size / 2, size * 0.55),
        (size - m, m * 1.15),
        (size - m, size - m),
    ]
    sw = max(1.5, size * 0.09)

    def line(x0: float, y0: float, x1: float, y1: float) -> None:
        steps = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        for i in range(steps + 1):
            t = i / steps
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            r = int(sw)
            for oy in range(-r - 1, r + 2):
                for ox in range(-r - 1, r + 2):
                    if ox * ox + oy * oy <= sw * sw:
                        setp(int(x + ox), int(y + oy), gold)

    for i in range(len(pts) - 1):
        line(*pts[i], *pts[i + 1])
    return px


def write_ico(path: Path, sizes: tuple[int, ...] = SIZES) -> None:
    images: list[tuple[int, bytes]] = []
    for s in sizes:
        images.append((s, _png_rgba(s, s, _monogram(s))))
    count = len(images)
    offset = 6 + 16 * count
    entries: list[bytes] = []
    data = bytearray()
    for s, png in images:
        w = 0 if s >= 256 else s
        h = 0 if s >= 256 else s
        entries.append(
            struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, len(png), offset + len(data))
        )
        data.extend(png)
    ico = struct.pack("<HHH", 0, 1, count) + b"".join(entries) + bytes(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(ico)


def main() -> int:
    write_ico(OUT_ICO)
    OUT_PNG.write_bytes(_png_rgba(256, 256, _monogram(256)))
    print(f"Wrote {OUT_ICO} ({OUT_ICO.stat().st_size} bytes)")
    print(f"Wrote {OUT_PNG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
