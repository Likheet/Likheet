"""The three plates of the profile: the header, the projects and open source.

Each comes wide (850 px) and for phones (390 px). They only show what grows: all-time totals,
projects and pull requests to other people's projects. No dates and nothing over time.
"""

from __future__ import annotations

import math

from art import scene
from art.scene import BLUSH, CARD, CORAL, CREAM
from art.svg import Motion, frame, glow, num, rng
from art.type import Typesetter, measure, sentences, wrap


def short(count: int) -> str:
    if count >= 10_000:
        return f"{count // 1000}k"
    if count >= 1000:
        return f"{count / 1000:.1f}".rstrip("0").rstrip(".") + "k"
    return str(count)


# ── header ──────────────────────────────────────────────────────────────────

def header(profile, mobile: bool = False) -> str:
    """The profile picture's world: a figure on a summit above the clouds at sunset, and who I am."""
    mo, ts, r = Motion(), Typesetter(), rng("header")
    width, height = (390, 440) if mobile else (850, 360)
    defs, body = [], []

    def add(part: tuple) -> None:
        defs.append(part[0])
        body.append(part[1])

    add(scene.sky("sky", width, height))
    body.append(scene.stars(r, mo, 0, width, 0, height * .5, 24 if mobile else 46))
    scale = .78 if mobile else 1
    rock_x, rock_w = width * (.6 if mobile else .72), 140 if mobile else 220
    top = height * .69
    add(scene.sun("sun", mo, rock_x, top, 210 if mobile else 290, colour="#ffcfa6", peak=.65))
    add(scene.clouds(r, mo, "c1", "wisp", width, height * .63, height, 22 * scale, 240, opacity=.6, swell=.4))
    add(scene.clouds(r, mo, "c2", "far", width, height * .69, height, 24 * scale, 170, swell=.5))
    body.append(scene.summit(r, rock_x, top, rock_w, height * .95))
    body.append(scene.figure(mo, rock_x + rock_w * .03, top + .4, 38 if mobile else 48))
    body.append(scene.birds(r, mo, rock_x - (90 if mobile else 130), top - 34, 3, 300 if mobile else 360, 30, 4, scale))
    body.append(scene.birds(r, mo, rock_x - 50, top - 70, 2, 260 if mobile else 300, 38, 21, .85 * scale))
    add(scene.clouds(r, mo, "c3", "mid", width, height * .81, height, 26 * scale, 110, swell=.35))
    add(scene.clouds(r, mo, "c4", "near", width, height * .93, height, 30 * scale, 70, swell=.5))

    stats = [f"{profile.contributions:,} contributions", f"{profile.pull_requests:,} pull requests",
             f"{profile.repositories} projects"]
    if mobile:
        body.append(ts.line(24, 62, profile.name, 34, CREAM, "light", tracking=-.01))
        for k, line in enumerate(wrap(profile.tagline, 15, "regular", width - 48, 2)):
            body.append(ts.line(24, 92 + k * 21, line, 15, BLUSH, "regular"))
        y = 92 + 21 * len(wrap(profile.tagline, 15, "regular", width - 48, 2)) + 12
        body.append(ts.line(24, y, "  ·  ".join(stats[:2]).upper(), 9.5, CREAM, "medium", tracking=.12, opacity=.75))
        body.append(ts.line(24, y + 17, stats[2].upper(), 9.5, CREAM, "medium", tracking=.12, opacity=.75))
    else:
        body.append(ts.line(56, 126, profile.name, 52, CREAM, "light", tracking=-.012))
        body.append(ts.line(58, 164, profile.tagline, 18, BLUSH, "regular"))
        body.append(ts.line(59, 202, "  ·  ".join(stats).upper(), 11, CREAM, "medium", tracking=.14, opacity=.75))

    desc = f"{profile.name}: {profile.tagline}. {', '.join(stats)}."
    return frame(width, height, "".join(body), "".join(defs) + ts.defs(), mo, profile.name, desc)


# ── projects ────────────────────────────────────────────────────────────────

def _vignette(project, mo: Motion, k: int, x: float, y: float, w: float, h: float) -> tuple:
    """A small painting of the same world for each project, different for every name and the same every day."""
    r = rng(project.name)
    defs, body = [], []

    def add(part: tuple) -> None:
        defs.append(part[0])
        body.append(part[1])

    shift = r.uniform(-.06, .06)
    stops = [(max(0, min(1, offset + shift)), colour) for offset, colour in scene.SKY]
    add(scene.sky(f"v{k}s", w, h, stops))
    body.append(scene.stars(r, mo, 0, w, 0, h * .4, 7))
    sun_x = w * r.uniform(.25, .8)
    add(scene.sun(f"v{k}g", mo, sun_x, h * .86, h * .9))
    add(scene.clouds(r, mo, f"v{k}a", "far", w, h * .58, h, 9, r.uniform(140, 200)))
    kind = r.choice(("summit", "peaks", "peaks"))
    if kind == "summit":
        px = w * r.uniform(.3, .7)
        body.append(scene.summit(r, px, h * .6, w * .36, h * .95))
        if r.random() < .6:
            body.append(scene.figure(mo, px + w * .01, h * .6 + .3, 17))
    else:
        for j in range(r.choice((1, 2, 3))):
            px, ph = w * r.uniform(.15, .85), h * r.uniform(.28, .48)
            peak_defs, peak_body, _ = scene.peak(r, f"v{k}p{j}", px, h * .82 - ph, h * .95)
            defs.append(peak_defs)
            body.append(peak_body)
    if r.random() < .5:
        body.append(scene.birds(r, mo, w * .15, h * .32, 2, w * .7, r.uniform(16, 24), r.uniform(0, 20), .55))
    add(scene.clouds(r, mo, f"v{k}b", r.choice(("mid", "near")), w, h * .8, h, 10, r.uniform(80, 130)))
    defs.append(f'<clipPath id="vc{k}"><rect width="{num(w)}" height="{num(h)}"/></clipPath>')
    return "".join(defs), (f'<g transform="translate({num(x)} {num(y)})"><g clip-path="url(#vc{k})">'
                           f'{"".join(body)}</g></g>')


def _fit(ts: Typesetter, x: float, y: float, text: str, size: float, width: float) -> str:
    """A name on one line, set smaller rather than cut when it is long."""
    natural = measure(text, size, "semibold")
    if natural > width:
        size = max(size * width / natural, size * .72)
    return ts.line(x, y, wrap(text, size, "semibold", width, 1)[0], size, CREAM, "semibold")


def _meta(project) -> list:
    """The small coral line under a project: status or language, then stars when there are enough."""
    if project.note:
        return [project.note.upper()] + ([project.link.upper()] if project.link else [])
    return [project.language.upper()] if project.language else []


def _meta_line(ts: Typesetter, x: float, y: float, project, size: float) -> str:
    parts, out = _meta(project), []
    text = "  ·  ".join(parts)
    out.append(ts.line(x, y, text, size, CORAL, "medium", tracking=.14))
    if project.stars:
        sx = x + (measure(text + "  ·  ", size, "medium", .14) if text else 0)
        out.append(scene.star_icon(sx, y, size * 1.05, CORAL))
        out.append(ts.line(sx + size * 1.05 + 4, y, short(project.stars), size, CORAL, "medium", tracking=.06))
    return "".join(out)


def projects(profile, mobile: bool = False) -> str:
    mo, ts = Motion(), Typesetter()
    items = profile.projects
    width = 390 if mobile else 850
    margin, gap = (20, 12) if mobile else (40, 18)
    title_y = 54 if mobile else 60
    top = 80 if mobile else 92
    defs, body = [], []
    defs.append(scene.gradient("night", scene.NIGHT))
    if mobile:
        card_w, card_h, columns, art_w = width - 2 * margin, 138, 1, 116
    else:
        columns = 3
        card_w, card_h, art_w = (width - 2 * margin - (columns - 1) * gap) / columns, 246, 0
    rows = math.ceil(len(items) / columns)
    height = round(top + rows * card_h + (rows - 1) * gap + (24 if mobile else 40))

    body.append(f'<rect width="{width}" height="{height}" fill="url(#night)"/>')
    body.append(scene.stars(rng("projects"), mo, 0, width, 0, top * .9, 14 if mobile else 30))
    body.append(ts.line(margin, title_y, "Projects", 26 if mobile else 30, CREAM, "light"))

    for k, project in enumerate(items):
        row, col = divmod(k, columns)
        x, y = margin + col * (card_w + gap), top + row * (card_h + gap)
        defs.append(f'<clipPath id="card{k}"><rect x="{num(x)}" y="{num(y)}" width="{num(card_w)}" '
                    f'height="{num(card_h)}" rx="12"/></clipPath>')
        art_h = card_h if mobile else 94
        art_defs, art = _vignette(project, mo, k, x, y, art_w or card_w, art_h)
        defs.append(art_defs)
        body.append(f'<g clip-path="url(#card{k})"><rect x="{num(x)}" y="{num(y)}" width="{num(card_w)}" '
                    f'height="{num(card_h)}" fill="{CARD}"/>{art}</g>')
        body.append(f'<rect x="{num(x + .5)}" y="{num(y + .5)}" width="{num(card_w - 1)}" height="{num(card_h - 1)}" '
                    f'rx="11.5" fill="none" stroke="{CREAM}" stroke-opacity=".08"/>')
        if mobile:
            tx, text_w = x + art_w + 16, card_w - art_w - 30
            body.append(_fit(ts, tx, y + 29, project.name, 15.5, text_w))
            for j, line in enumerate(sentences(project.description, 12.3, "regular", text_w, 4)):
                body.append(ts.line(tx, y + 49 + j * 16.5, line, 12.3, "#d9cfe9", "regular"))
            body.append(_meta_line(ts, tx, y + card_h - 15, project, 9))
        else:
            tx, text_w = x + 18, card_w - 36
            body.append(_fit(ts, tx, y + 94 + 31, project.name, 17, text_w))
            for j, line in enumerate(sentences(project.description, 13, "regular", text_w, 4)):
                body.append(ts.line(tx, y + 94 + 54 + j * 17.5, line, 13, "#d9cfe9", "regular"))
            body.append(_meta_line(ts, tx, y + card_h - 18, project, 9.5))

    desc = " ".join(f"{p.name}: {p.description}" for p in items)
    return frame(width, height, "".join(body), "".join(defs) + ts.defs(), mo, "Projects", desc)


# ── open source ─────────────────────────────────────────────────────────────

DUSK = [(0, "#211a50"), (.3, "#3b3078"), (.55, "#65438a"), (.75, "#a64d6c"), (.9, "#dc5a5a"), (1, "#ef6b58")]


def _range(pulls: list, mo: Motion, ts: Typesetter, r, k0: int, left: float, right: float, sea: float,
           low: float, high: float, mobile: bool) -> tuple:
    """One mountain range: a peak per project, the biggest in the middle, labelled above its summit."""
    defs, back, front, labels = [], [], [], []
    count = len(pulls)
    step = (right - left) / count
    order = sorted(range(count), key=lambda i: abs(i - (count - 1) / 2))   # middle slots first
    slots = {}
    for rank, slot in enumerate(order):
        slots[rank] = left + step * (slot + .5)
    big = math.log10(max(p.stars for p in pulls) + 1)
    small = math.log10(min(p.stars for p in pulls) + 1)
    drawn = []
    for rank, pr in enumerate(pulls):
        share = 1 if big == small else (math.log10(pr.stars + 1) - small) / (big - small)
        rise = low + (high - low) * share
        x = slots[rank] + r.uniform(-.12, .12) * step
        peak_defs, peak_body, summit_x = scene.peak(r, f"p{k0 + rank}", x, sea - rise, sea + 60)
        defs.append(peak_defs)
        drawn.append((rise, peak_body, pr, summit_x, sea - rise, rank))
    # the tallest go behind
    for rise, peak_body, *_ in sorted(drawn, key=lambda d: -d[0]):
        back.append(peak_body)
    placed = []
    name_size, star_size = (12, 9.5) if mobile else (13.5, 10.5)
    for rise, _, pr, sx, top, rank in sorted(drawn, key=lambda d: d[3]):
        delay = rank * .37
        if pr.merged:
            front.append(scene.flag(mo, sx, top, delay))
        if pr.open:
            ly = top + rise * .42
            lx = sx + rise * .2
            trail = [(lx + rise * .18, top + rise * .8), (lx + rise * .05, top + rise * .62), (lx, ly)]
            front.append(scene.lantern(mo, "lamp", lx, ly, trail, delay))
        label_y = top - (24 if pr.merged else 10)
        name_w = measure(pr.name, name_size, "semibold")
        box = (sx - name_w / 2 - 6, sx + name_w / 2 + 6)
        while any(box[0] < b and a < box[1] and abs(label_y - y) < 30 for a, b, y in placed):
            label_y -= 30
        placed.append((box[0], box[1], label_y))
        labels.append(ts.line(sx, label_y - star_size - 6, pr.name, name_size, CREAM, "semibold", anchor="middle"))
        figure = short(pr.stars)
        figure_w = star_size * 1.05 + 4 + measure(figure, star_size, "medium")
        fx = sx - figure_w / 2
        labels.append(scene.star_icon(fx, label_y, star_size * 1.05, BLUSH, .85))
        labels.append(ts.line(fx + star_size * 1.05 + 4, label_y, figure, star_size, BLUSH, "medium", opacity=.85))
    return defs, "".join(back), "".join(front), "".join(labels)


def _legend(ts: Typesetter, mo: Motion, x: float, y: float, anchor_right: bool) -> str:
    size = 9.5
    merged, review = "MERGED", "IN REVIEW"
    w_merged = 12 + measure(merged, size, "medium", .14)
    w_review = 14 + measure(review, size, "medium", .14)
    start = x - (w_merged + 18 + w_review) if anchor_right else x
    out = [f'<path d="M{num(start + 1)} {num(y + 1)}v-11" stroke="{CREAM}" stroke-width="1.1"/>'
           f'<path d="M{num(start + 1.4)} {num(y - 10)}l7 2.2-7 2.2Z" fill="{CORAL}"/>',
           ts.line(start + 12, y, merged, size, BLUSH, "medium", tracking=.14, opacity=.8)]
    lx = start + w_merged + 18
    out.append(f'<circle cx="{num(lx + 4)}" cy="{num(y - 3.5)}" r="7" fill="url(#lamp)"/>'
               f'<circle cx="{num(lx + 4)}" cy="{num(y - 3.5)}" r="1.6" fill="#fff3dc"/>')
    out.append(ts.line(lx + 14, y, review, size, BLUSH, "medium", tracking=.14, opacity=.8))
    return "".join(out)


def open_source(profile, mobile: bool = False) -> str:
    mo, ts, r = Motion(), Typesetter(), rng("open-source")
    pulls = profile.open_source
    width = 390 if mobile else 850
    margin = 22 if mobile else 40
    caption = f"Pull requests to projects with {short(profile.open_source_stars)} stars between them"
    rows = [pulls[:4], pulls[4:8]] if mobile and len(pulls) > 4 else [pulls]
    row_h = 210
    height = (150 + row_h * len(rows) + 10) if mobile else 430
    defs, body = [scene.gradient("dusk", DUSK), glow("lamp", "#ffd9ad", .9)], []
    body.append(f'<rect width="{width}" height="{height}" fill="url(#dusk)"/>')
    body.append(scene.stars(r, mo, 0, width, 0, height * .5, 22 if mobile else 50))
    sun_defs, sun_body = scene.sun("sun", mo, width * .8, height * .97, 260 if mobile else 340, peak=.55)
    defs.append(sun_defs)
    body.append(sun_body)

    if mobile:
        body.append(ts.line(margin, 52, "Open source", 26, CREAM, "light"))
        lines = wrap(caption, 13.5, "regular", width - 2 * margin, 2)
        for k, line in enumerate(lines):
            body.append(ts.line(margin, 78 + k * 19, line, 13.5, BLUSH, "regular", opacity=.9))
        body.append(_legend(ts, mo, margin, 78 + len(lines) * 19 + 14, False))
    else:
        body.append(ts.line(margin, 60, "Open source", 30, CREAM, "light"))
        body.append(ts.line(margin, 87, caption, 15, BLUSH, "regular", opacity=.9))
        body.append(_legend(ts, mo, width - margin, 60, True))

    if not pulls:
        body.append(ts.line(margin, 140, "Nothing here yet", 15, BLUSH, "regular"))
    for k, group in enumerate(rows):
        if not group:
            continue
        sea = (150 + row_h * (k + 1) - 26) if mobile else height * .83
        low, high = (48, 112) if mobile else (70, 200)
        cloud_defs, haze = scene.clouds(r, mo, f"h{k}", "far", width, sea - (high * .55), height, 12, 200, opacity=.55)
        defs.append(cloud_defs)
        body.append(haze)
        range_defs, back, front, labels = _range(group, mo, ts, r, k * 10, margin, width - margin, sea, low, high,
                                                 mobile)
        defs += range_defs
        body += [back, front]
        for layer, offset, size, seconds in (("mid", 0, 12, 120), ("near", 28, 14, 80)):
            cloud_defs, bank = scene.clouds(r, mo, f"s{k}{layer}", layer, width, sea + offset, height, size, seconds)
            defs.append(cloud_defs)
            body.append(bank)
        body.append(labels)
    body.append(scene.birds(r, mo, width * .12, height * .34, 3, width * .45, 40, 12, .8))

    desc = caption + ". " + " ".join(
        f"{p.owner}/{p.name} ({short(p.stars)} stars): {'merged' if p.merged else ''}"
        f"{' and ' if p.merged and p.open else ''}{'in review' if p.open else ''}." for p in pulls)
    return frame(width, height, "".join(body), "".join(defs) + ts.defs(), mo, "Open source", desc)
