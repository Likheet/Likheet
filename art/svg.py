"""SVG basics shared by the cards."""

from __future__ import annotations

from xml.sax.saxutils import escape


def num(value: float, places: int = 1) -> str:
    """A number for SVG: rounded, without trailing zeros, never "-0"."""
    text = f"{round(value, places):.{places}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def esc(text: str) -> str:
    return escape(str(text), {'"': "&quot;"})
