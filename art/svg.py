"""SVG basics shared by every plate: numbers, motion and the frame."""

from __future__ import annotations

import random
import zlib
from xml.sax.saxutils import escape


def num(value: float, places: int = 1) -> str:
    """A number for SVG: rounded, without trailing zeros, never "-0"."""
    text = f"{round(value, places):.{places}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def esc(text: str) -> str:
    return escape(str(text), {'"': "&quot;"})


def rng(seed: str) -> random.Random:
    """A random source that gives the same drawing for the same seed on every run."""
    return random.Random(zlib.crc32(seed.encode()))


def gradient(gid: str, stops: list, vertical: bool = True, user: tuple = ()) -> str:
    """A linear gradient. stops are (offset, colour[, opacity]); user=(x1, y1, x2, y2) sets it in plate units."""
    if user:
        x1, y1, x2, y2 = user
        where = f'gradientUnits="userSpaceOnUse" x1="{num(x1)}" y1="{num(y1)}" x2="{num(x2)}" y2="{num(y2)}"'
    else:
        where = 'x2="0" y2="1"' if vertical else 'x2="1" y2="0"'
    out = []
    for stop in stops:
        offset, colour = stop[0], stop[1]
        alpha = f' stop-opacity="{num(stop[2], 2)}"' if len(stop) > 2 and stop[2] < 1 else ""
        out.append(f'<stop offset="{num(offset, 3)}" stop-color="{colour}"{alpha}/>')
    return f'<linearGradient id="{gid}" {where}>{"".join(out)}</linearGradient>'


def glow(gid: str, colour: str, peak: float = 1.0) -> str:
    """A radial gradient that fades from colour to nothing."""
    return (f'<radialGradient id="{gid}"><stop offset="0" stop-color="{colour}" stop-opacity="{num(peak, 2)}"/>'
            f'<stop offset=".45" stop-color="{colour}" stop-opacity="{num(peak * .35, 2)}"/>'
            f'<stop offset="1" stop-color="{colour}" stop-opacity="0"/></radialGradient>')


# Every animation is ambient: an animated element rests where it is drawn and only moves around it,
# so the picture is complete the moment it loads and stays complete with motion turned off.
# A CSS animation replaces an element's transform attribute, so animated elements sit inside
# translated groups instead of carrying a transform of their own.
ANIMATIONS = {
    "drift": ".drift{animation:drift var(--t) linear infinite}@keyframes drift{to{transform:translateX(var(--dx))}}",
    "fly": ".fly{animation:fly var(--t) linear var(--d) infinite}@keyframes fly{0%{transform:translate(0,0);"
           "opacity:0}12%,82%{opacity:1}to{transform:translate(var(--dx),var(--dy));opacity:0}}",
    "flap": ".flap{animation:flap var(--t) ease-in-out var(--d) infinite}@keyframes flap{50%{transform:scaleY(.25)}}",
    "tw": ".tw{animation:tw var(--t) ease-in-out var(--d) infinite}@keyframes tw{50%{opacity:.15}}",
    "breathe": ".breathe{animation:breathe 9s ease-in-out infinite}@keyframes breathe{50%{opacity:.7}}",
    "wave": ".wave{animation:wave 2.8s ease-in-out infinite}@keyframes wave{50%{transform:rotate(-8deg) scale(.9,1.12)}}",
    "flutter": ".flutter{animation:flutter 1.3s ease-in-out var(--d) infinite}"
               "@keyframes flutter{50%{transform:scale(.7,1.08)}}",
    "pulse": ".pulse{animation:pulse 2.6s ease-in-out var(--d) infinite}@keyframes pulse{50%{opacity:.3}}",
}


class Motion:
    def __init__(self) -> None:
        self._used: dict = {}

    def __call__(self, name: str, **variables) -> str:
        """Attributes that attach animation `name`; variables become CSS custom properties (t=40 -> --t:40s)."""
        self._used[name] = ANIMATIONS[name]
        style = ";".join(f"--{key}:{value}" for key, value in variables.items())
        return f' class="{name}"' + (f' style="{style}"' if style else "")

    def css(self) -> str:
        body = "".join(self._used.values())
        return f"@media (prefers-reduced-motion:no-preference){{{body}}}" if body else ""


def frame(width: int, height: int, body: str, defs: str, motion: Motion, title: str, desc: str,
          radius: int = 14) -> str:
    """A complete, accessible SVG with rounded corners that clip whatever drifts past them."""
    css = motion.css()
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" '
            f'height="{height}" role="img" aria-labelledby="t d"><title id="t">{esc(title)}</title>'
            f'<desc id="d">{esc(desc)}</desc><defs>{defs}<clipPath id="frame"><rect width="{width}" '
            f'height="{height}" rx="{radius}"/></clipPath>' + (f"<style>{css}</style>" if css else "")
            + f'</defs><g clip-path="url(#frame)">{body}</g></svg>')
