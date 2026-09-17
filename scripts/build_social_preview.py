#!/usr/bin/env python3
"""Render the test site's branded 1200 x 630 social-share image."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH = 1200
HEIGHT = 630
BACKGROUND = "#050505"
OFF_WHITE = "#f4f3ef"
GOLD = "#c99a3d"


def bold_font_path() -> Path:
    candidates = (
        Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("A supported bold font was not found")


def fit_font(draw: ImageDraw.ImageDraw, text: str, font_path: Path, max_width: int) -> ImageFont.FreeTypeFont:
    for size in range(48, 25, -1):
        font = ImageFont.truetype(str(font_path), size=size)
        left, _, right, _ = draw.textbbox((0, 0), text, font=font)
        if right - left <= max_width:
            return font
    return ImageFont.truetype(str(font_path), size=26)


def tracked_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, spacing: int) -> int:
    widths = [draw.textlength(character, font=font) for character in text]
    return round(sum(widths) + spacing * max(0, len(text) - 1))


def draw_tracked_text(
    draw: ImageDraw.ImageDraw,
    position: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: str,
    spacing: int,
) -> None:
    x, y = position
    for character in text:
        draw.text((x, y), character, font=font, fill=fill)
        x += round(draw.textlength(character, font=font)) + spacing


def render(logo_path: Path, output_path: Path) -> None:
    canvas = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(canvas)

    # Keep every important element well inside social-platform crop-safe margins.
    draw.rounded_rectangle((28, 28, WIDTH - 29, HEIGHT - 29), radius=18, outline="#24211b", width=2)
    draw.line((82, 54, WIDTH - 82, 54), fill=GOLD, width=3)

    logo = Image.open(logo_path).convert("RGB")
    logo.thumbnail((790, 421), Image.Resampling.LANCZOS)
    logo_x = (WIDTH - logo.width) // 2
    canvas.paste(logo, (logo_x, 66))

    font_path = bold_font_path()
    headline = "Find Christian Hip-Hop Shows & Festivals"
    headline_font = fit_font(draw, headline, font_path, 1010)
    headline_box = draw.textbbox((0, 0), headline, font=headline_font)
    headline_width = headline_box[2] - headline_box[0]
    draw.text(
        ((WIDTH - headline_width) // 2, 496),
        headline,
        font=headline_font,
        fill=OFF_WHITE,
    )

    site = "KINGDOMCIRCUIT.COM"
    site_font = ImageFont.truetype(str(font_path), size=19)
    site_spacing = 3
    site_width = tracked_width(draw, site, site_font, site_spacing)
    site_x = (WIDTH - site_width) // 2
    site_y = 560
    draw_tracked_text(draw, (site_x, site_y), site, site_font, GOLD, site_spacing)
    line_y = site_y + 12
    draw.line((84, line_y, site_x - 30, line_y), fill="#795d27", width=2)
    draw.line((site_x + site_width + 30, line_y, WIDTH - 84, line_y), fill="#795d27", width=2)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, "PNG", optimize=True)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "test-overrides" / "assets" / "social-preview.png",
    )
    args = parser.parse_args()
    render(root / "assets" / "logo.png", args.output.resolve())


if __name__ == "__main__":
    main()
