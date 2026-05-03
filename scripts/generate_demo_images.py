"""Optional: generate solid-color placeholder images (no real fish).

The repository ships with **real Wikimedia Commons photos** in `data/demo_images/`
(see `data/demo_images/SOURCES.md`). Use this script only if you need offline
placeholders without downloading Commons assets — e.g. in a restricted network.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SPECIES_COLORS: dict[str, tuple[int, int, int]] = {
    "red_snapper": (200, 50, 50),
    "southern_flounder": (139, 119, 80),
    "spotted_seatrout": (100, 140, 120),
    "red_drum": (180, 90, 40),
    "black_drum": (60, 60, 60),
    "king_mackerel": (70, 130, 180),
    "cobia": (90, 70, 50),
    "shark": (120, 130, 140),
}

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "demo_images"


def generate() -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for name, color in SPECIES_COLORS.items():
        img = Image.new("RGB", (800, 600), color)
        draw = ImageDraw.Draw(img)
        label = name.replace("_", " ").title()
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
        except (OSError, IOError):
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), label, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((800 - tw) / 2, (600 - th) / 2), label, fill=(255, 255, 255), font=font)
        draw.text((20, 560), "DEMO PLACEHOLDER — NOT A REAL FISH PHOTO", fill=(200, 200, 200))
        path = OUTPUT_DIR / f"{name}.jpg"
        img.save(path, quality=85)
        paths.append(path)
    return paths


if __name__ == "__main__":
    for p in generate():
        print(p)
