#!/usr/bin/env python3
"""Generate the transparent-circle test favicon package from the supplied logo."""

from __future__ import annotations

import pathlib

from PIL import Image, ImageDraw


ROOT = pathlib.Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "test-overrides" / "assets"
SOURCE = ASSET_DIR / "favicon-kc-stacked-v1-source.png"
OUTPUTS = {
    "favicon-kc-stacked-v2-source.png": 150,
    "favicon-kc-stacked-v2-48.png": 48,
    "favicon-kc-stacked-v2-96.png": 96,
    "favicon-kc-stacked-v2-180.png": 180,
    "favicon-kc-stacked-v2-192.png": 192,
    "favicon-kc-stacked-v2-512.png": 512,
    "favicon-kc-stacked-v2-maskable-512.png": 512,
}
SUPERSAMPLE = 4


def circle_mask(size: int) -> Image.Image:
    high_size = size * SUPERSAMPLE
    high_mask = Image.new("L", (high_size, high_size), 0)
    ImageDraw.Draw(high_mask).ellipse(
        (0, 0, high_size - 1, high_size - 1),
        fill=255,
    )
    return high_mask.resize((size, size), Image.Resampling.LANCZOS)


def generate() -> None:
    source = Image.open(SOURCE).convert("RGB")
    for filename, size in OUTPUTS.items():
        artwork = source.resize((size, size), Image.Resampling.LANCZOS).convert("RGBA")
        artwork.putalpha(circle_mask(size))
        artwork.save(ASSET_DIR / filename, format="PNG", optimize=True)


if __name__ == "__main__":
    generate()
