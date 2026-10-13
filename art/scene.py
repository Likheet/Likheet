"""The world of the plates: the scene of the profile picture, a figure on a summit above a sea of
sunset clouds. Colours are sampled from the avatar.

Clouds drift, the scarf blows, birds cross and stars twinkle. Every piece is drawn where it rests,
so a plate is complete the moment it loads and with motion turned off.
"""

from __future__ import annotations

import math

from art.svg import Motion, glow, gradient, num

# sampled from the avatar, top of the sky to the clouds
SKY = [(0, "#2a2363"), (.28, "#4a3c87"), (.48, "#654386"), (.62, "#8a4a79"), (.75, "#c84e62"),
       (.87, "#ec5556"), (1, "#f67459")]
CREAM = "#fff4ee"     # main text
BLUSH = "#ffd6c9"     # secondary text
CORAL = "#ff8d70"     # accents, the scarf
INK = "#1d1436"       # silhouettes
PLUM = "#4a2447"      # birds
NIGHT = [(0, "#211a4b"), (1, "#2d2358")]
CARD = "#2f2660"

# cloud layers, far to near: highlight on top, body below
CLOUDS = {
    "wisp": ("#a575ad", "#7a4a88"),
    "far": ("#f6a08e", "#d65e6d"),
    "mid": ("#ffa886", "#ea5a56"),
    "near": ("#ffbd97", "#e2524e"),
}


def sky(gid: str, width: float, height: float, stops: list = SKY) -> tuple:
    return gradient(gid, stops), f'<rect width="{num(width)}" height="{num(height)}" fill="url(#{gid})"/>'


def stars(r, mo: Motion, x0: float, x1: float, y0: float, y1: float, count: int) -> str:
    """Small stars, a third of them twinkling at their own pace."""
    still, lit = [], []
    for _ in range(count):
        x, y = r.uniform(x0, x1), r.uniform(y0, y1)
        size, alpha = r.uniform(.45, 1.25), r.uniform(.3, .85) * (1 - (y - y0) / max(y1 - y0, 1) * .6)
        dot = f'<circle cx="{num(x)}" cy="{num(y)}" r="{num(size, 2)}" fill="{CREAM}" fill-opacity="{num(alpha, 2)}"'
        if r.random() < .35:
            lit.append(dot + mo("tw", t=f"{num(r.uniform(3, 7))}s", d=f"-{num(r.uniform(0, 7))}s") + "/>")
        else:
            still.append(dot + "/>")
    return "".join(still + lit)


def sun(gid: str, mo: Motion, cx: float, cy: float, radius: float, colour: str = "#ffc39c",
        peak: float = .6) -> tuple:
    return (glow(gid, colour, peak),
            f'<circle cx="{num(cx)}" cy="{num(cy)}" r="{num(radius)}" fill="url(#{gid})"{mo("breathe")}/>')


def mix(a: str, b: str, t: float) -> str:
    """Colour a blended over colour b; t=1 gives a."""
    pa, pb = (int(a[i:i + 2], 16) for i in (1, 3, 5)), (int(b[i:i + 2], 16) for i in (1, 3, 5))
    return "#" + "".join(f"{round(x * t + y * (1 - t)):02x}" for x, y in zip(pa, pb))


def _discs(circles: list) -> str:
    """Path data for many circles, so a whole cloud layer is one element."""
    out = []
    for x, y, r in circles:
        r = max(round(r), 1)
        out.append(f"M{round(x) - r} {round(y)}a{r} {r} 0 1 0 {2 * r} 0a{r} {r} 0 1 0 {-2 * r} 0")
    return "".join(out)


def clouds(r, mo: Motion, gid: str, layer: str, period: float, top: float, bottom: float, size: float,
           seconds: float, opacity: float = 1, swell: float = .6) -> tuple:
    """A sea of billowing cloud heaps that tiles every `period` pixels and drifts right one period per cycle.

    Each heap is shaded on its own, lit at the crown and deep at the foot, and the lower heaps are
    drawn over the higher ones, so the sea reads as heaps piled in front of each other. The heaps
    are defined once and placed four times side by side; the sea below them is filled to `bottom`.
    """
    light, body = CLOUDS[layer]
    deep = mix(body, "#4a2350", .72)
    defs = [gradient(gid, [(0, light), (.4, body), (1, deep)]),
            gradient(gid + "s", [(0, body), (1, deep)], user=(0, top, 0, bottom))]
    waves, phase = r.choice((1, 2)), r.uniform(0, 2 * math.pi)
    heaps, x = [], 0.0
    while x < period:
        radius = size * r.uniform(.8, 1.4)
        rise = swell * size * (.5 + .5 * math.sin(2 * math.pi * waves * x / period + phase))
        crown = top - rise + size * r.uniform(-.4, .5)
        circles = [(x, crown + radius, radius)]
        for side in (-1, 1):
            circles.append((x + side * radius * r.uniform(.7, 1), crown + radius * r.uniform(1.25, 1.5),
                            radius * r.uniform(.55, .78)))
        circles.append((x + r.choice((-1, 1)) * radius * r.uniform(.25, .45), crown + radius * r.uniform(.35, .5),
                        radius * r.uniform(.45, .6)))
        heaps.append((crown, circles))
        x += radius * r.uniform(1.05, 1.45)
    heaps.sort(key=lambda heap: heap[0])
    paths = "".join(f'<path d="{_discs(circles)}"/>' for _, circles in heaps)
    defs.append(f'<g id="{gid}h" fill="url(#{gid})">{paths}</g>')
    base = top + size * .8
    sea = (f'<rect x="{num(-2 * period - size * 3)}" y="{num(base)}" width="{num(4 * period + size * 6)}" '
           f'height="{num(max(bottom - base, 0))}" fill="url(#{gid}s)"/>')
    copies = "".join(f'<use href="#{gid}h" x="{num(k * period)}"/>' for k in (-2, -1, 0, 1))
    alpha = f' opacity="{num(opacity, 2)}"' if opacity < 1 else ""
    drawing = f'<g{alpha}><g{mo("drift", t=f"{num(seconds)}s", dx=f"{num(period)}px")}>{sea}{copies}</g></g>'
    return "".join(defs), drawing


def summit(r, cx: float, top: float, width: float, base: float) -> str:
    """The low dark rock the figure stands on: flat on top, rounding off into the clouds, lit along its crest."""
    w, h = width / 2, base - top

    def side(sign: int) -> list:
        points = []
        for k in range(1, 13):
            t = k / 12
            rough = r.uniform(-1, 1) * h * .04 if k > 1 else 0
            points.append((cx + sign * w * (.12 + .88 * t), top + h * .95 * t ** 2.2 + rough))
        return points

    crown = [(cx - w * .12, top + 1.4), (cx - w * .04, top + .3), (cx + w * .05, top), (cx + w * .12, top + 1)]
    outline = side(-1)[::-1] + crown + side(1)
    edge = "M" + "L".join(f"{num(x)} {num(y)}" for x, y in outline[3:-3])
    return (f'<path d="{_poly(outline)}" fill="{INK}"/>'
            f'<path d="{edge}" fill="none" stroke="{CORAL}" stroke-width="1.2" stroke-opacity=".6" '
            f'stroke-linejoin="round"/>')


def figure(mo: Motion, x: float, feet: float, height: float = 34) -> str:
    """The figure from the profile picture, standing on the summit with its scarf blowing in the wind."""
    s = height / 34
    body = ("M-3.6-25.8C-3.9-21-3.4-17.5-3.2-14.5L-3.3-.2H-1.4L-.5-12.4H.5L1.4-.2H3.3L3.2-14.5"
            "C3.4-17.5 3.9-21 3.6-25.8Q0-27.9-3.6-25.8Z"
            "M-3.6-25.3-5-15.4h1.1L-2.8-22Z M3.6-25.3 5-15.4H3.9L2.8-22Z"
            "M-1-28.6h2v2.4h-2Z")
    scarf = ("M0 0C5-2.8 9.5 1.8 15-.8 19.5-2.9 23 .6 30-.6 26.5 1.6 22.8 2.6 18.6 2.2"
             " 14 1.8 10.4 4.4 5.6 3.9 3.4 3.7 1.6 2.9 0 2.2Z"
             "M2 1.4C6 3 9.4 6 14.6 5.6 11 7.4 6.6 6.8 3.4 4.6Z")
    return (f'<g transform="translate({num(x)} {num(feet)}) scale({num(s, 3)})">'
            f'<g transform="translate(.6 -26.4)"><g{mo("wave")}><path d="{scarf}" fill="{CORAL}"/></g></g>'
            f'<path d="{body}" fill="{INK}"/><circle cy="-30.9" r="2.9" fill="{INK}"/></g>')


def birds(r, mo: Motion, x: float, y: float, count: int, travel: float, seconds: float, start: float,
          scale: float = 1) -> str:
    """A small flock gliding right from (x, y), fading in and out, its birds flapping out of step."""
    flock = []
    for k in range(count):
        bx, by = -k * r.uniform(10, 16) * scale, r.uniform(-8, 8) * scale
        flap = mo("flap", t=f"{num(r.uniform(.8, 1.2), 2)}s", d=f"-{num(r.random(), 2)}s")
        flock.append(f'<g transform="translate({num(bx)} {num(by)}) scale({num(scale * r.uniform(.8, 1.15), 2)})">'
                     f'<path{flap} d="M-6 .4Q-3-3.6 0 0Q3-3.6 6 .4" fill="none" stroke="{PLUM}" '
                     f'stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></g>')
    glide = mo("fly", t=f"{num(seconds)}s", d=f"-{num(start)}s", dx=f"{num(travel)}px",
               dy=f"{num(-travel * r.uniform(.03, .1))}px")
    return f'<g transform="translate({num(x)} {num(y)})"><g{glide}>{"".join(flock)}</g></g>'


def _slope(r, ax: float, ay: float, bx: float, by: float, steps: int, jag: float) -> list:
    """Points from a to b with the middle ones pushed about, for a broken mountain edge."""
    points = [(ax, ay)]
    for k in range(1, steps):
        t = k / steps
        nx, ny = by - ay, -(bx - ax)
        length = math.hypot(nx, ny) or 1
        push = r.uniform(-jag, jag) * math.sin(math.pi * t)
        points.append((ax + (bx - ax) * t + nx / length * push, ay + (by - ay) * t + ny / length * push))
    return points + [(bx, by)]


def _at_height(points: list, y: float) -> tuple:
    """Where a polyline going down from the summit first reaches height y."""
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        if (ay - y) * (by - y) <= 0 and ay != by:
            t = (y - ay) / (by - ay)
            return ax + (bx - ax) * t, y
    return points[-1]


def _poly(points: list) -> str:
    return "M" + "L".join(f"{num(x)} {num(y)}" for x, y in points) + "Z"


def peak(r, gid: str, x: float, top: float, base: float, lit: str = "#e87a78") -> tuple:
    """A mountain lit from the right by a low sun: a shaded face, a glowing face and alpenglow snow."""
    height = base - top
    half = height * r.uniform(.95, 1.25)
    summit_x = x + r.uniform(-.06, .06) * half
    left = _slope(r, summit_x, top, x - half, base, 7, height * .05)
    right = _slope(r, summit_x, top, x + half, base, 7, height * .05)
    ridge = _slope(r, summit_x, top, x + half * r.uniform(.05, .3), base, 6, height * .04)
    shade = left + ridge[::-1]
    glow_face = ridge + right[::-1]
    snow_y = top + height * r.uniform(.16, .24)
    lx, _ = _at_height(left, snow_y)
    mx, _ = _at_height(ridge, snow_y)
    rx, _ = _at_height(right, snow_y)

    def cap(edge_a: list, edge_b: list, xa: float, xb: float) -> list:
        """The part of a face above the snow line, with a ragged lower edge."""
        upper_a = [p for p in edge_a if p[1] < snow_y]
        upper_b = [p for p in edge_b if p[1] < snow_y]
        zig = [(xa + (xb - xa) * t, snow_y + r.uniform(-1, 1) * height * .035 * math.sin(math.pi * t))
               for t in (.25, .5, .75)]
        return upper_a + [(xa, snow_y)] + zig + [(xb, snow_y)] + upper_b[::-1]

    defs = gradient(gid, [(0, lit), (.55, "#8e4470"), (1, "#3b2659")], user=(0, top, 0, base))
    drawing = (f'<path d="{_poly(shade)}" fill="#2b1f4f"/>'
               f'<path d="{_poly(glow_face)}" fill="url(#{gid})"/>'
               f'<path d="{_poly(cap(left, ridge, lx, mx))}" fill="#6b4c93"/>'
               f'<path d="{_poly(cap(ridge, right, mx, rx))}" fill="#ffc6b2"/>')
    return defs, drawing, summit_x


def flag(mo: Motion, x: float, y: float, delay: float) -> str:
    """Planted on a summit: a pull request that was merged."""
    return (f'<path d="M{num(x)} {num(y)}v-17" stroke="{CREAM}" stroke-width="1.2" stroke-linecap="round"/>'
            f'<g transform="translate({num(x + .4)} {num(y - 16.6)})"><g{mo("flutter", d=f"-{num(delay, 2)}s")}>'
            f'<path d="M0 0L11 3.3 0 6.6Z" fill="{CORAL}"/></g></g>')


def lantern(mo: Motion, gid: str, x: float, y: float, trail: list, delay: float) -> str:
    """A climber's light on the way up: a pull request still in review."""
    path = "M" + "L".join(f"{num(px)} {num(py)}" for px, py in trail)
    return (f'<path d="{path}" fill="none" stroke="#ffd9ad" stroke-opacity=".45" stroke-width="1" '
            f'stroke-dasharray="1.5 3" stroke-linecap="round"/>'
            f'<circle cx="{num(x)}" cy="{num(y)}" r="9" fill="url(#{gid})"{mo("pulse", d=f"-{num(delay, 2)}s")}/>'
            f'<circle cx="{num(x)}" cy="{num(y)}" r="1.7" fill="#fff3dc"/>')


def star_icon(x: float, y: float, size: float, fill: str, opacity: float = 1) -> str:
    """A five-pointed star with its baseline at y, for stargazer counts (the font has no ★)."""
    points = []
    for k in range(10):
        angle = -math.pi / 2 + k * math.pi / 5
        radius = size / 2 if k % 2 == 0 else size / 2 * .45
        points.append((x + size / 2 + math.cos(angle) * radius, y - size * .46 + math.sin(angle) * radius))
    alpha = f' fill-opacity="{num(opacity, 2)}"' if opacity < 1 else ""
    return f'<path d="{_poly(points)}" fill="{fill}"{alpha}/>'
