"""Monospaced text as glyph outlines, so the cards look the same in every browser and app.

Each glyph a card uses is defined once in <defs> and placed with <use>. Every character is
0.6 em wide, spaces included, so text lines up in columns as in a terminal. The typeface is
Source Code Pro (fonts/, SIL Open Font License).
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

from art.svg import num

FONTS = Path(__file__).resolve().parent.parent / "fonts"
FILES = {False: "SourceCodePro-Regular.ttf", True: "SourceCodePro-Bold.ttf"}
ADVANCE = .6        # width of every character, in ems
ELLIPSIS = "…"


@lru_cache(maxsize=None)
def _font(bold: bool) -> tuple:
    tt = TTFont(FONTS / FILES[bold])
    return tt.getBestCmap(), tt.getGlyphSet(), tt["head"].unitsPerEm


@lru_cache(maxsize=None)
def _outline(bold: bool, glyph: str) -> str:
    _, glyphs, _ = _font(bold)
    pen = SVGPathPen(glyphs, ntos=lambda v: num(v, 0))
    glyphs[glyph].draw(TransformPen(pen, (1, 0, 0, -1, 0, 0)))
    return pen.getCommands()


def fit(text: str, chars: int) -> str:
    """The text cut to `chars` characters, ending in an ellipsis if it was longer."""
    text = " ".join(str(text).split())
    return text if len(text) <= chars else text[:chars - 1].rstrip(" ,;:-") + ELLIPSIS


def clause(text: str, chars: int) -> str:
    """The text cut to `chars` characters, preferably where a clause ends, ending in an ellipsis if cut."""
    text = " ".join(str(text).split())
    if len(text) <= chars:
        return text
    head = text[:chars - 1]
    cut = max(head.rfind(", "), head.rfind("; "), head.rfind(" ("), head.rfind(" - "))
    if cut >= chars * .55:
        return head[:cut].rstrip(" ,;:-") + ELLIPSIS
    return fit(text, chars)


def first_sentence(text: str) -> str:
    parts = re.split(r"(?<=[.!?])\s", " ".join(str(text).split()), maxsplit=1)
    return parts[0]


class Typesetter:
    """Sets text for one SVG and remembers which glyph outlines it used."""

    def __init__(self) -> None:
        self._defs: dict = {}

    def line(self, x: float, y: float, text: str, size: float, fill: str, bold: bool = False,
             opacity: float = 1, attrs: str = "") -> str:
        """One line with its baseline at y. A character the font lacks keeps its cell, left blank."""
        cmap, _, upm = _font(bold)
        uses = []
        for k, ch in enumerate(text):
            glyph = cmap.get(ord(ch))
            if ch == " " or glyph is None or not _outline(bold, glyph):
                continue
            gid = ("b" if bold else "r") + re.sub(r"[^A-Za-z0-9_-]", "_", glyph)
            self._defs.setdefault(gid, _outline(bold, glyph))
            pen = k * ADVANCE * upm
            uses.append(f'<use href="#{gid}" x="{num(pen, 0)}"/>' if pen else f'<use href="#{gid}"/>')
        if not uses:
            return ""
        alpha = f' fill-opacity="{num(opacity, 2)}"' if opacity < 1 else ""
        return (f'<g transform="translate({num(x)} {num(y)}) scale({num(size / upm, 5)})" fill="{fill}"{alpha}{attrs}>'
                f'{"".join(uses)}</g>')

    def defs(self) -> str:
        return "".join(f'<path id="{gid}" d="{d}"/>' for gid, d in self._defs.items())
