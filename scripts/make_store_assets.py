#!/usr/bin/env python3
"""Generate Rebble App Store icons, banner, and emery screenshots."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "store"
CATALOG = ROOT / "spider_catalog.csv"
COLOR = ROOT / "resources" / "images" / "color"
MONO = ROOT / "resources" / "images" / "mono"
MENU_ICON = ROOT / "resources" / "images" / "icon.png"
W, H = 200, 228


def load_catalog() -> dict[str, dict[str, str]]:
    with CATALOG.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return {r["filename"].replace(".png", ""): r for r in rows}


def watchface_frame(
    plate: Image.Image,
    common: str,
    scientific: str,
    *,
    dark: bool = False,
) -> Image.Image:
    bg = (0, 0, 0) if dark else (255, 255, 255)
    fg = (255, 255, 255) if dark else (0, 0, 0)
    sub = (200, 200, 200) if dark else (60, 60, 60)
    out = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(out)
    try:
        font_b = ImageFont.truetype("DejaVuSans-Bold.ttf", 15)
        font_s = ImageFont.truetype("DejaVuSans.ttf", 12)
        font_t = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
        font_d = ImageFont.truetype("DejaVuSans.ttf", 12)
    except OSError:
        font_b = font_s = font_t = font_d = ImageFont.load_default()

    plate = plate.copy()
    px = Image.new("RGB", plate.size, bg)
    px.paste(plate, mask=None)
    out.paste(px, (6, 14))

    def center_text(y: int, text: str, font, fill) -> None:
        tw = draw.textlength(text, font=font)
        draw.text(((W - tw) / 2, y), text, fill=fill, font=font)

    center_text(122, common[:28], font_b, fg)
    center_text(142, scientific, font_s, sub)
    now = datetime.now()
    time_str = now.strftime("%-I:%M" if now.hour <= 12 else "%H:%M").lstrip("0") or "12"
    center_text(162, time_str, font_t, fg)
    center_text(208, now.strftime("%a, %b %-d"), font_d, sub)
    return out


def icon_from_plate(path: Path, size: int) -> Image.Image:
    with Image.open(path) as im:
        im = im.convert("RGBA")
    canvas = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    im.thumbnail((size - 8, size - 8), Image.Resampling.LANCZOS)
    x = (size - im.width) // 2
    y = (size - im.height) // 2
    canvas.paste(im, (x, y), im if im.mode == "RGBA" else None)
    return canvas.convert("RGB")


def make_banner() -> Image.Image:
    banner = Image.new("RGB", (720, 320), (28, 26, 24))
    draw = ImageDraw.Draw(banner)
    try:
        title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 56)
        sub_font = ImageFont.truetype("DejaVuSans.ttf", 22)
    except OSError:
        title_font = sub_font = ImageFont.load_default()

    plate_path = COLOR / "salticidae.png"
    with Image.open(plate_path) as im:
        im = im.convert("RGBA")
    im = im.resize((320, int(320 * im.height / im.width)), Image.Resampling.LANCZOS)
    banner.paste(im, (380, 20), im)

    draw.text((32, 48), "Spinneret", fill=(245, 240, 232), font=title_font)
    draw.text((32, 120), "71 spider families · Pebble Time 2", fill=(180, 175, 168), font=sub_font)
    draw.text((32, 155), "Field-guide plates on your wrist", fill=(140, 135, 128), font=sub_font)
    draw.rectangle((32, 220, 340, 224), fill=(120, 90, 160))
    draw.text((32, 238), "Color · grayscale · preview cycle", fill=(160, 155, 148), font=sub_font)
    return banner


def main() -> None:
    cat = load_catalog()
    STORE.mkdir(parents=True, exist_ok=True)
    (STORE / "screenshots").mkdir(exist_ok=True)

    hero = COLOR / "salticidae.png"
    icon_from_plate(hero, 25).save(MENU_ICON)
    STORE.joinpath("watch_menu_icon_25.png").write_bytes(MENU_ICON.read_bytes())
    icon_from_plate(hero, 48).save(STORE / "icon_48x48.png")
    icon_from_plate(hero, 80).save(STORE / "icon_80x80.png")
    icon_from_plate(hero, 144).save(STORE / "icon_144x144.png")
    make_banner().save(STORE / "banner_720x320.png", optimize=True)

    shots = [
        ("emery_color_salticidae.png", "salticidae", False, COLOR),
        ("emery_color_lycosidae.png", "lycosidae", False, COLOR),
        ("emery_color_theraphosidae.png", "theraphosidae", False, COLOR),
        ("emery_mono_salticidae.png", "salticidae", False, MONO),
        ("emery_dark_araneidae.png", "araneidae", True, COLOR),
    ]
    for name, slug, dark, folder in shots:
        meta = cat[slug]
        with Image.open(folder / f"{slug}.png") as plate:
            frame = watchface_frame(
                plate,
                meta["common"],
                meta["scientific"],
                dark=dark,
            )
            frame.save(STORE / "screenshots" / name, optimize=True)

    print(f"Store assets written to {STORE}/")


if __name__ == "__main__":
    main()