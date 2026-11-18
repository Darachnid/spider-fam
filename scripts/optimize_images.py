#!/usr/bin/env python3
"""Build Pebble RGB222 color + grayscale assets from spider family illustrations."""

from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "spider_catalog.csv"
ORIGINALS = ROOT / "originals"
ASSETS_GLOB = Path("/home/manjo/.cursor/projects/home-manjo-Pebble/assets")
COLOR_OUT = ROOT / "resources" / "images" / "color"
MONO_OUT = ROOT / "resources" / "images" / "mono"
REFERENCE_OUT = ROOT / "resources" / "images" / "reference"
ICON_OUT = ROOT / "resources" / "images" / "icon.png"
MAX_SIZE = (188, 106)
CHANNELS = (0, 85, 170, 255)
PALETTE = [v for r in CHANNELS for g in CHANNELS for b in CHANNELS for v in (r, g, b)]
PALETTE_IMAGE = Image.new("P", (1, 1))
PALETTE_IMAGE.putpalette(PALETTE + [0] * (768 - len(PALETTE)))
NO_DITHER = Image.Dither.NONE

COMMON: dict[str, str] = {
    "agelenidae": "Funnel weavers",
    "amaurobiidae": "Hackledmesh weavers",
    "amphinectidae": "Stiphidiid spiders",
    "anapidae": "Minute orb-weavers",
    "antrodiaetidae": "Folding-trapdoor spiders",
    "anyphaenidae": "Anyphaenid sac spiders",
    "araneidae": "Orb-weavers",
    "atypidae": "Purse-web spiders",
    "caponiidae": "Caponiid spiders",
    "cithaeronidae": "Cithaeronid spiders",
    "clubionidae": "Sac spiders",
    "corinnidae": "Corinnid sac spiders",
    "ctenidae": "Wandering spiders",
    "ctenizidae": "Trapdoor spiders",
    "cybaeidae": "Cybaeid spiders",
    "deinopidae": "Ogre-faced spiders",
    "desidae": "Desid intertidal spiders",
    "dictynidae": "Dictynid spiders",
    "diguetidae": "Diguetid spiders",
    "dipluridae": "Funnel-web tarantulas",
    "dysderidae": "Woodlouse hunters",
    "euctenizidae": "Wafer-lid trapdoor spiders",
    "eutichuridae": "Eutichurid sac spiders",
    "filistatidae": "Crevice weavers",
    "gnaphosidae": "Ground spiders",
    "hahniidae": "Dwarf sheet weavers",
    "hersiliidae": "Two-tailed spiders",
    "homalonychidae": "Homalonychid ground spiders",
    "hypochilidae": "Lampshade spiders",
    "leptonetidae": "Leptonetid spiders",
    "linyphiidae": "Sheetweavers",
    "liocranidae": "Liocranid sac spiders",
    "lycosidae": "Wolf spiders",
    "mecicobothriidae": "Dwarf tarantulas",
    "mimetidae": "Pirate spiders",
    "miturgidae": "Miturgid spiders",
    "mysmenidae": "Dwarf orb-weavers",
    "nemesiidae": "Nemesiid trapdoor spiders",
    "nephilidae": "Golden orb-weavers",
    "nesticidae": "Cave cobweb spiders",
    "ochyroceratidae": "Ochyroceratid spiders",
    "oecobiidae": "Wall spiders",
    "oonopidae": "Goblin spiders",
    "oxyopidae": "Lynx spiders",
    "philodromidae": "Running crab spiders",
    "pholcidae": "Cellar spiders",
    "phrurolithidae": "Phrurolithid ground spiders",
    "pimoidae": "Pimoid sheet weavers",
    "pisauridae": "Nursery-web spiders",
    "plectreuridae": "Plectreurid spiders",
    "prodidomidae": "Prodidomid ground spiders",
    "salticidae": "Jumping spiders",
    "scytodidae": "Spitting spiders",
    "segestriidae": "Tube-dwelling spiders",
    "selenopidae": "Flattie spiders",
    "sicariidae": "Recluse spiders",
    "sparassidae": "Huntsman spiders",
    "symphytognathidae": "Symphytognathid dwarf spiders",
    "telemidae": "Telemid sheet weavers",
    "tetragnathidae": "Long-jawed orb-weavers",
    "theraphosidae": "Tarantulas",
    "theridiidae": "Cobweb spiders",
    "theridiosomatidae": "Ray spiders",
    "thomisidae": "Crab spiders",
    "titanoecidae": "Titanoecid spiders",
    "trachelidae": "Widow's-thrill spiders",
    "trechaleidae": "Trechaleid spiders",
    "trogloraptoridae": "Trogloraptor spiders",
    "uloboridae": "Cribellate orb-weavers",
    "zodariidae": "Ant spiders",
    "zoropsidae": "Zoropsid spiders",
}


def family_slug(path: Path) -> str | None:
    name = path.name.lower()
    if not name.endswith(".png") or name.startswith("screenshot"):
        return None
    slug = name.split("-", 1)[0]
    return slug if slug.endswith("idae") else None


def scientific(slug: str) -> str:
    return slug[0].upper() + slug[1:]


def strip_plate_label(image: Image.Image) -> Image.Image:
    """Remove the family name printed along the bottom of field-guide plates."""
    gray = image.convert("L")
    width, height = gray.size
    x0, x1 = int(width * 0.08), int(width * 0.92)
    scan_floor = int(height * 0.78)
    label_top = height
    in_band = False
    for y in range(height - 1, scan_floor, -1):
        row = [gray.getpixel((x, y)) for x in range(x0, x1, 4)]
        dark = sum(1 for value in row if value < 210)
        if dark >= max(3, len(row) // 25):
            in_band = True
            label_top = y
        elif in_band:
            break
    if label_top >= height:
        return image
    pad = 6
    return image.crop((0, 0, width, max(scan_floor, label_top - pad)))


def discover_sources() -> list[Path]:
    found: dict[str, Path] = {}
    for path in sorted(ASSETS_GLOB.glob("*.png")):
        slug = family_slug(path)
        if slug and slug in COMMON:
            found[slug] = path
    missing = sorted(set(COMMON) - set(found))
    if missing:
        raise SystemExit(f"Missing illustrations for: {', '.join(missing)}")
    return [found[s] for s in sorted(found)]


def prepare_rgb(source: Path, *, margin: int, contrast: float, color: float) -> Image.Image:
    with Image.open(source) as raw:
        rgba = ImageOps.exif_transpose(raw).convert("RGBA")
        background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        background.alpha_composite(rgba)
        image = background.convert("RGB")

    image = strip_plate_label(image)

    difference = ImageOps.invert(image.convert("L"))
    mask = difference.point(lambda p: 255 if p > 20 else 0)
    bounds = mask.getbbox()
    if bounds:
        x0, y0, x1, y1 = bounds
        width, height = image.size
        bounds = (
            max(0, x0 - margin),
            max(0, y0 - margin),
            min(width, x1 + margin),
            min(height, y1 + margin),
        )
        image = image.crop(bounds)

    image.thumbnail(MAX_SIZE, Image.Resampling.LANCZOS)
    image = ImageEnhance.Contrast(image).enhance(contrast)
    image = ImageEnhance.Color(image).enhance(color)
    return image


def quantize_fit(image: Image.Image, *, grayscale: bool) -> Image.Image:
    work = ImageOps.grayscale(image).convert("RGB") if grayscale else image
    indexed = work.quantize(palette=PALETTE_IMAGE, dither=NO_DITHER)
    canvas = Image.new("RGB", MAX_SIZE, (255, 255, 255))
    x = (MAX_SIZE[0] - work.width) // 2
    y = (MAX_SIZE[1] - work.height) // 2
    canvas.paste(indexed.convert("RGB"), (x, y))
    return canvas


def write_catalog(sources: list[Path]) -> None:
    rows: list[dict[str, str]] = []
    for path in sources:
        slug = family_slug(path)
        assert slug
        filename = f"{slug}.png"
        rows.append(
            {
                "original": path.name,
                "common": COMMON[slug],
                "scientific": scientific(slug),
                "filename": filename,
                "resource": f"SPIDER_{slug.upper()}",
            }
        )
    with CATALOG.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["original", "common", "scientific", "filename", "resource"],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contrast", type=float, default=1.08)
    parser.add_argument("--color", type=float, default=1.12)
    parser.add_argument("--margin", type=int, default=14)
    args = parser.parse_args()

    sources = discover_sources()
    ORIGINALS.mkdir(parents=True, exist_ok=True)
    for path in (COLOR_OUT, MONO_OUT, REFERENCE_OUT):
        path.mkdir(parents=True, exist_ok=True)

    for source in sources:
        slug = family_slug(source)
        assert slug
        ref = ORIGINALS / f"{slug}.png"
        if not ref.exists():
            shutil.copy2(source, ref)
        rgb = prepare_rgb(ref, margin=args.margin, contrast=args.contrast, color=args.color)
        dest = f"{slug}.png"
        quantize_fit(rgb, grayscale=False).save(COLOR_OUT / dest, optimize=True)
        quantize_fit(rgb, grayscale=True).save(MONO_OUT / dest, optimize=True)
        shutil.copy2(ref, REFERENCE_OUT / dest)
        print(f"OK: {slug}")

    write_catalog(sources)
    if not ICON_OUT.exists():
        sample = COLOR_OUT / "salticidae.png"
        if sample.is_file():
            Image.open(sample).resize((25, 25), Image.Resampling.LANCZOS).save(ICON_OUT)
    print(f"Wrote {len(sources)} families to resources/images/{{color,mono}}/")


if __name__ == "__main__":
    main()