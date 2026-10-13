"""Text as glyph outlines, so every plate looks the same in every browser.

Each glyph a plate uses is defined once in <defs> and placed with <use>.
Widths come from the font itself (advances and pair kerning), so lines can
be measured and wrapped exactly. The typeface is Hanken Grotesk (fonts/,
SIL Open Font License).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

from art.svg import num

FONTS = Path(__file__).resolve().parent.parent / "fonts"
STYLES = {"light": "Light", "regular": "Regular", "medium": "Medium", "semibold": "SemiBold"}
ELLIPSIS = "…"


class Font:
    def __init__(self, style: str) -> None:
        self.style = style
        self.tt = TTFont(FONTS / f"HankenGrotesk-{STYLES[style]}.ttf")
        self.upm = self.tt["head"].unitsPerEm
        self.cmap = self.tt.getBestCmap()
        self.glyphs = self.tt.getGlyphSet()
        self.hmtx = self.tt["hmtx"]
        self.pairs = self._pair_tables()

    def _pair_tables(self) -> list:
        """The pair-kerning subtables of the GPOS 'kern' feature, in lookup order."""
        if "GPOS" not in self.tt:
            return []
        gpos = self.tt["GPOS"].table
        indices = sorted({i for record in gpos.FeatureList.FeatureRecord if record.FeatureTag == "kern"
                          for i in record.Feature.LookupListIndex})
        tables = []
        for i in indices:
            lookup = gpos.LookupList.Lookup[i]
            for sub in lookup.SubTable:
                sub = sub.ExtSubTable if lookup.LookupType == 9 else sub
                if sub.LookupType == 2:
                    tables.append(sub)
        return tables

    @lru_cache(maxsize=None)
    def kern(self, left: str, right: str) -> int:
        for sub in self.pairs:
            if left not in sub.Coverage.glyphs:
                continue
            if sub.Format == 1:
                pairs = sub.PairSet[sub.Coverage.glyphs.index(left)].PairValueRecord
                for record in pairs:
                    if record.SecondGlyph == right:
                        return getattr(record.Value1, "XAdvance", 0) or 0
            else:
                c1 = sub.ClassDef1.classDefs.get(left, 0)
                c2 = sub.ClassDef2.classDefs.get(right, 0)
                value = sub.Class1Record[c1].Class2Record[c2].Value1
                return getattr(value, "XAdvance", 0) or 0 if value else 0
        return 0

    def name(self, ch: str):
        return self.cmap.get(ord(ch))

    def advance(self, glyph: str) -> int:
        return self.hmtx[glyph][0]

    @lru_cache(maxsize=None)
    def outline(self, glyph: str) -> str:
        pen = SVGPathPen(self.glyphs, ntos=lambda v: num(v, 0))
        self.glyphs[glyph].draw(TransformPen(pen, (1, 0, 0, -1, 0, 0)))
        return pen.getCommands()


@lru_cache(maxsize=None)
def font(style: str) -> Font:
    return Font(style)


def _clean(text: str) -> str:
    """The text with every character the font cannot draw left out."""
    f = font("regular")
    kept = "".join(ch if f.name(ch) else " " for ch in str(text))
    return " ".join(kept.split())


def _layout(text: str, f: Font, tracking: float):
    """(glyph, pen position) for each character, and the total advance, in font units."""
    pens, pen, prev = [], 0.0, None
    for ch in text:
        glyph = f.name(ch)
        if glyph is None:
            continue
        if prev is not None:
            pen += f.kern(prev, glyph) + tracking * f.upm
        pens.append((glyph, pen))
        pen += f.advance(glyph)
        prev = glyph
    return pens, pen


def measure(text: str, size: float, style: str = "regular", tracking: float = 0) -> float:
    """Width in pixels. tracking is extra space between letters, in ems."""
    f = font(style)
    return _layout(_clean(text), f, tracking)[1] * size / f.upm


def _ellipsize(line: str, size: float, style: str, width: float) -> str:
    line = line.rstrip(" ,;:")
    while line and measure(line + ELLIPSIS, size, style) > width:
        line = line[:-1].rstrip(" ,;:")
    return line + ELLIPSIS


def wrap(text: str, size: float, style: str, width: float, max_lines: int = 2) -> list:
    """Lines no wider than width; the last ends in an ellipsis if the text was cut."""
    words, lines, current = _clean(text).split(), [], ""
    for word in words:
        candidate = f"{current} {word}" if current else word
        if not current or measure(candidate, size, style) <= width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines - 1] + [_ellipsize(" ".join(lines[max_lines - 1:]), size, style, width)]
    return [line if measure(line, size, style) <= width else _ellipsize(line, size, style, width) for line in lines]


def sentences(text: str, size: float, style: str, width: float, max_lines: int) -> list:
    """As many whole sentences as fit in max_lines; cut with an ellipsis only if the first does not fit."""
    parts = [part if part.endswith((".", "!", "?")) else part + "." for part in _clean(text).split(". ") if part]
    for count in range(len(parts), 0, -1):
        lines = wrap(" ".join(parts[:count]), size, style, width, max_lines=99)
        if len(lines) <= max_lines:
            return lines
    return wrap(text, size, style, width, max_lines)


class Typesetter:
    """Sets text for one SVG and remembers which glyph outlines it used."""

    def __init__(self) -> None:
        self._defs: dict = {}

    def line(self, x: float, y: float, text: str, size: float, fill: str, style: str = "regular",
             anchor: str = "start", tracking: float = 0, opacity: float = 1, attrs: str = "") -> str:
        """One line of text with its baseline at y. anchor is start, middle or end."""
        f = font(style)
        pens, total = _layout(_clean(text), f, tracking)
        if not pens:
            return ""
        scale = size / f.upm
        width = total * scale
        left = x - (width if anchor == "end" else width / 2 if anchor == "middle" else 0)
        uses = []
        for glyph, pen in pens:
            if not f.outline(glyph):
                continue
            gid = f"{style[0]}{glyph}".replace(".", "_")
            self._defs.setdefault(gid, f.outline(glyph))
            uses.append(f'<use href="#{gid}" x="{num(pen, 0)}"/>' if pen else f'<use href="#{gid}"/>')
        alpha = f' fill-opacity="{num(opacity, 2)}"' if opacity < 1 else ""
        return (f'<g transform="translate({num(left)} {num(y)}) scale({num(scale, 5)})" fill="{fill}"{alpha}{attrs}>'
                f'{"".join(uses)}</g>')

    def defs(self) -> str:
        return "".join(f'<path id="{gid}" d="{d}"/>' for gid, d in self._defs.items())

