"""The profile picture as a dither in its own colours, with light rippling across it.

The avatar is reduced to a grid and dithered (Floyd–Steinberg) into a small palette sampled from
the avatar, and each cell is drawn as a round dot. The dots are grouped into diagonal bands that
dim and brighten one after another, so a slow wave of light runs across the picture while the
picture itself stays put. After dither-portrait by Harkirat Singh
(github.com/0xharkirat/dither-portrait).
"""

from __future__ import annotations

import io
import math

import requests
from PIL import Image, ImageOps

from art.svg import num

# deep sky to bright cloud, sampled from the avatar; the first is the background and is not drawn
PALETTE = ["#1b1438", "#3f3380", "#6c4588", "#c44b62", "#f2665a", "#ffa47f", "#ffd9c2"]
BANDS = 12          # diagonal bands of the travelling light
SECONDS = 6


def _rgb(colour: str) -> tuple:
    return tuple(int(colour[i:i + 2], 16) for i in (1, 3, 5))


def _distance(a: tuple, b: tuple) -> float:
    """'Redmean' colour distance: cheap and closer to how eyes compare colours than plain RGB."""
    mean = (a[0] + b[0]) / 2
    dr, dg, db = a[0] - b[0], a[1] - b[1], a[2] - b[2]
    return math.sqrt((2 + mean / 256) * dr * dr + 4 * dg * dg + (2 + (255 - mean) / 256) * db * db)


def avatar(url: str, size: int = 460) -> Image.Image:
    response = requests.get(url, params={"s": size}, timeout=30)
    response.raise_for_status()
    return Image.open(io.BytesIO(response.content)).convert("RGB")


def dither(image: Image.Image, grid: int, palette: list = PALETTE) -> list:
    """Rows of palette indices: the image at grid x grid, Floyd–Steinberg dithered into the palette."""
    small = ImageOps.autocontrast(image, cutoff=1).resize((grid, grid), Image.LANCZOS)
    colours = [_rgb(c) for c in palette]
    work = [[list(small.getpixel((x, y))) for x in range(grid)] for y in range(grid)]
    out = [[0] * grid for _ in range(grid)]
    for y in range(grid):
        for x in range(grid):
            old = tuple(max(0, min(255, v)) for v in work[y][x])
            best = min(range(len(colours)), key=lambda i: _distance(old, colours[i]))
            out[y][x] = best
            error = [o - c for o, c in zip(old, colours[best])]
            for dx, dy, share in ((1, 0, 7 / 16), (-1, 1, 3 / 16), (0, 1, 5 / 16), (1, 1, 1 / 16)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < grid and ny < grid:
                    for c in range(3):
                        work[ny][nx][c] += error[c] * share
    return out


def _dots(points: list) -> str:
    """Path data with a dot at each (x, y) cell, in cell units, using relative moves along a row."""
    out, px, py = [], None, None
    for x, y in sorted(points, key=lambda p: (p[1], p[0])):
        out.append(f"m{x - px} 0h0" if py == y else f"M{x} {y}h0")
        px, py = x, y
    return "".join(out)


def svg(cells: list, size: float, palette: list = PALETTE, dot: float = .86) -> tuple:
    """(css, markup) for the dither drawn in a size x size square at the origin."""
    grid = len(cells)
    groups = {}
    for y, row in enumerate(cells):
        for x, colour in enumerate(row):
            if colour:
                band = int(((x * 1.3 + y * .7) / (grid * 2)) * BANDS * 2) % BANDS
                groups.setdefault((band, colour), []).append((x, y))
    css = (f".rip{{animation:rip {num(SECONDS)}s ease-in-out infinite}}"
           "@keyframes rip{0%,100%{opacity:1}50%{opacity:.5}}")
    paths = "".join(
        f'<path class="rip" style="animation-delay:-{num(SECONDS * band / BANDS, 2)}s" '
        f'stroke="{palette[colour]}" d="{_dots(points)}"/>'
        for (band, colour), points in sorted(groups.items()))
    scale = size / grid
    markup = (f'<rect width="{num(size)}" height="{num(size)}" fill="{palette[0]}"/>'
              f'<g transform="translate({num(scale / 2, 3)} {num(scale / 2, 3)}) scale({num(scale, 4)})" '
              f'fill="none" stroke-width="{dot}" stroke-linecap="round">{paths}</g>')
    return css, markup
