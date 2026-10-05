"""Draws osmbot's own icon (a simple football on green; original artwork, safe to publish).

``python tools/make_icon.py`` writes ``tools/assets/osmbot.ico``. Needs Pillow (``pip install pillow``).
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 1024  # drawn large, then scaled down for the smaller icon sizes
OUT = Path(__file__).resolve().parent / "assets" / "osmbot.ico"


def polygon(centre: tuple[float, float], radius: float, sides: int = 5, rotation: float = -90.0):
    return [
        (centre[0] + radius * math.cos(math.radians(rotation + 360 * i / sides)),
         centre[1] + radius * math.sin(math.radians(rotation + 360 * i / sides)))
        for i in range(sides)
    ]


def draw() -> Image.Image:
    image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    canvas = ImageDraw.Draw(image)
    canvas.rounded_rectangle((0, 0, SIZE - 1, SIZE - 1), radius=SIZE // 5, fill=(24, 104, 58, 255))
    centre = (SIZE / 2, SIZE / 2)
    ball = SIZE * 0.36
    canvas.ellipse((centre[0] - ball, centre[1] - ball, centre[0] + ball, centre[1] + ball),
                   fill=(250, 250, 250, 255), outline=(20, 20, 20, 255), width=SIZE // 60)
    inner = polygon(centre, ball * 0.36)
    canvas.polygon(inner, fill=(20, 20, 20, 255))
    for i, point in enumerate(inner):  # seams from the centre patch to the edge, and an edge patch at each end
        angle = math.radians(-90 + 72 * i)
        edge = (centre[0] + ball * 0.96 * math.cos(angle), centre[1] + ball * 0.96 * math.sin(angle))
        canvas.line((point, edge), fill=(20, 20, 20, 255), width=SIZE // 60)
        patch = (centre[0] + ball * 0.8 * math.cos(angle), centre[1] + ball * 0.8 * math.sin(angle))
        canvas.polygon(polygon(patch, ball * 0.17, rotation=-90 + 72 * i + 180), fill=(20, 20, 20, 255))
    return image


if __name__ == "__main__":
    OUT.parent.mkdir(exist_ok=True)
    draw().save(OUT, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"Icone criado: {OUT}")
