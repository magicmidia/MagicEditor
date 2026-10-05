#!/usr/bin/env python3
"""Generate resources/icons/app/magiceditor.ico (multi-size editor glyph).

Luminous Arcane Monogram: Code chevrons (< >) forming an 'M' with a radiant
central magic sparkle star (✦) and vertical caret beam over an obsidian squircle.

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
OUT_SVG = ROOT / "resources" / "icons" / "app" / "magiceditor.svg"
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


def _cov(sd: float) -> float:
    return max(0.0, min(1.0, 0.5 - sd))


def _sd_round_rect(
    px: float, py: float, cx: float, cy: float, hw: float, hh: float, rad: float
) -> float:
    qx = abs(px - cx) - hw + rad
    qy = abs(py - cy) - hh + rad
    outside = (max(qx, 0.0) ** 2 + max(qy, 0.0) ** 2) ** 0.5
    inside = min(max(qx, qy), 0.0)
    return outside + inside - rad


def _sd_segment(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    pax, pay = px - ax, py - ay
    bax, bay = bx - ax, by - ay
    h = max(0.0, min(1.0, (pax * bax + pay * bay) / (bax * bax + bay * bay + 1e-9)))
    dx = pax - bax * h
    dy = pay - bay * h
    return (dx * dx + dy * dy) ** 0.5


def _sd_star_4(px: float, py: float, cx: float, cy: float, r_out: float) -> float:
    dx = abs(px - cx)
    dy = abs(py - cy)
    return ((dx**0.6 + dy**0.6) ** (1.0 / 0.6)) - r_out


def _blend(
    dst: tuple[int, int, int, int],
    rgb: tuple[int, int, int],
    cover: float,
) -> tuple[int, int, int, int]:
    if cover <= 0.002:
        return dst
    sr, sg, sb = rgb
    dr, dg, db, da = dst
    sa = cover
    da_f = da / 255.0
    out_a = sa + da_f * (1.0 - sa)
    if out_a <= 0.0:
        return (0, 0, 0, 0)
    out_r = (sr * sa + dr * da_f * (1.0 - sa)) / out_a
    out_g = (sg * sa + dg * da_f * (1.0 - sa)) / out_a
    out_b = (sb * sa + db * da_f * (1.0 - sa)) / out_a
    return (
        int(out_r + 0.5),
        int(out_g + 0.5),
        int(out_b + 0.5),
        int(out_a * 255.0 + 0.5),
    )


def render_editor_icon(size: int) -> list[tuple[int, int, int, int]]:
    """Render the Arcane Monogram M icon at the given size."""
    px = [(0, 0, 0, 0)] * (size * size)
    cx = cy = (size - 1) / 2.0
    margin = size * 0.065
    radius = size * 0.22
    hw = hh = size / 2.0 - margin

    w_span = size * 0.32
    h_top = cy - size * 0.24
    h_bot = cy + size * 0.26
    h_mid = cy + size * 0.04

    stroke = max(1.2, size * 0.088)
    half_s = stroke / 2.0

    x_left = cx - w_span
    x_right = cx + w_span

    # 4 segments forming the 'M' from code chevrons
    segs = [
        (x_left, h_bot, x_left, h_top),  # Left vertical stem
        (x_left, h_top, cx, h_mid),  # Left diagonal
        (cx, h_mid, x_right, h_top),  # Right diagonal
        (x_right, h_top, x_right, h_bot),  # Right vertical stem
    ]

    star_cx = cx
    star_cy = cy - size * 0.12
    star_r = max(1.5, size * 0.14)
    caret_top = h_mid
    caret_bot = h_bot
    caret_w = max(1.2, size * 0.07)

    for y in range(size):
        for x in range(size):
            p = x + 0.5
            q = y + 0.5

            # 1. Base tile squircle
            d_tile = _sd_round_rect(p, q, cx, cy, hw, hh, radius)
            if d_tile > 1.5:
                continue
            cov_tile = _cov(d_tile)

            # Deep obsidian gradient
            t_grad = q / size
            r_bg = int(15 * (1.0 - t_grad) + 9 * t_grad)
            g_bg = int(18 * (1.0 - t_grad) + 11 * t_grad)
            b_bg = int(28 * (1.0 - t_grad) + 16 * t_grad)

            color = _blend((0, 0, 0, 0), (r_bg, g_bg, b_bg), cov_tile)

            # Ambient golden glow
            dist_c = ((p - cx) ** 2 + (q - cy) ** 2) ** 0.5
            glow = max(0.0, 1.0 - dist_c / (size * 0.55)) ** 2
            if glow > 0:
                color = _blend(color, (255, 180, 20), glow * 0.18 * cov_tile)

            # Subtle top rim highlight
            d_rim = abs(d_tile + 1.2) - 0.7
            if d_rim < 0.5:
                rim_cov = _cov(d_rim) * max(0.0, 1.0 - q / (size * 0.6))
                color = _blend(color, (255, 225, 120), rim_cov * 0.32)

            # 2. Monogram M strokes
            d_m = min(_sd_segment(p, q, ax, ay, bx, by) for ax, ay, bx, by in segs) - half_s
            cov_m = _cov(d_m)

            if cov_m > 0:
                vert_t = max(0.0, min(1.0, (q - h_top) / (h_bot - h_top + 1e-5)))
                r_gold = int(255 * (1.0 - vert_t * 0.05))
                g_gold = int(230 * (1.0 - vert_t * 0.32))
                b_gold = int(130 * (1.0 - vert_t * 0.72))
                color = _blend(color, (r_gold, g_gold, b_gold), cov_m)

            # 3. Center Caret beam
            d_caret = _sd_segment(p, q, star_cx, caret_top, star_cx, caret_bot) - (caret_w / 2.0)
            cov_caret = _cov(d_caret)
            if cov_caret > 0:
                color = _blend(color, (255, 240, 180), cov_caret * 0.95)

            # 4. Central Magic Sparkle Star ✦
            d_star = _sd_star_4(p, q, star_cx, star_cy, star_r)
            cov_star = _cov(d_star)
            if cov_star > 0:
                color = _blend(color, (255, 255, 255), cov_star)

            px[y * size + x] = color

    return px


def write_ico(path: Path, sizes: tuple[int, ...] = SIZES) -> None:
    images: list[tuple[int, bytes]] = []
    for s in sizes:
        images.append((s, _png_rgba(s, s, render_editor_icon(s))))
    count = len(images)
    offset = 6 + 16 * count
    entries: list[bytes] = []
    data = bytearray()
    for s, png in images:
        w = 0 if s >= 256 else s
        h = 0 if s >= 256 else s
        entries.append(struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, len(png), offset + len(data)))
        data.extend(png)
    ico = struct.pack("<HHH", 0, 1, count) + b"".join(entries) + bytes(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(ico)


def generate_svg() -> str:
    """Generate modern crisp vector SVG of the MagicEditor emblem."""
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"
     width="100%" height="100%">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#121520"/>
      <stop offset="100%" stop-color="#08090D"/>
    </linearGradient>
    <radialGradient id="goldGlow" cx="50%" cy="45%" r="55%">
      <stop offset="0%" stop-color="#FFD700" stop-opacity="0.22"/>
      <stop offset="60%" stop-color="#F59E0B" stop-opacity="0.06"/>
      <stop offset="100%" stop-color="#000000" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="goldStem" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#FFF1B8"/>
      <stop offset="45%" stop-color="#FFD000"/>
      <stop offset="100%" stop-color="#E67E00"/>
    </linearGradient>
    <linearGradient id="rimGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#FFE082" stop-opacity="0.45"/>
      <stop offset="50%" stop-color="#6B7280" stop-opacity="0.15"/>
      <stop offset="100%" stop-color="#1F2937" stop-opacity="0.05"/>
    </linearGradient>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#000000" flood-opacity="0.55"/>
    </filter>
  </defs>

  <!-- Base Squircle Plate -->
  <rect x="16" y="16" width="224" height="224" rx="52" fill="url(#bgGrad)" filter="url(#shadow)"/>
  <rect x="16" y="16" width="224" height="224" rx="52" fill="url(#goldGlow)"/>
  <rect x="16.5" y="16.5" width="223" height="223" rx="51.5"
        fill="none" stroke="url(#rimGrad)" stroke-width="1.5"/>

  <!-- Arcane Monogram "M" composed of Code Chevrons -->
  <path d="M 46 194 L 46 66 L 128 138 L 210 66 L 210 194"
        fill="none"
        stroke="url(#goldStem)"
        stroke-width="22"
        stroke-linecap="round"
        stroke-linejoin="round"/>

  <!-- Vertical Caret Beam -->
  <line x1="128" y1="138" x2="128" y2="194"
        stroke="#FFF8E1"
        stroke-width="16"
        stroke-linecap="round"/>

  <!-- Magic Sparkle Core (4-Point Diamond Star ✦) -->
  <path d="M 128 62 C 128 85, 137 98, 160 98 C 137 98, 128 111, 128 134
           C 128 111, 119 98, 96 98 C 119 98, 128 85, 128 62 Z"
        fill="#FFFFFF"/>
  <!-- Sparkle Amber Halo -->
  <circle cx="128" cy="98" r="7" fill="#FFE082" opacity="0.8"/>
</svg>
"""


def main() -> int:
    write_ico(OUT_ICO)
    OUT_PNG.write_bytes(_png_rgba(256, 256, render_editor_icon(256)))
    OUT_SVG.write_text(generate_svg(), encoding="utf-8")
    print(f"Wrote {OUT_ICO} ({OUT_ICO.stat().st_size} bytes)")
    print(f"Wrote {OUT_PNG} ({OUT_PNG.stat().st_size} bytes)")
    print(f"Wrote {OUT_SVG} ({OUT_SVG.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
