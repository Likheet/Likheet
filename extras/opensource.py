"""Open source: pull requests to other people's projects, as a short star catalogue.

Each pull request is drawn as the star of its project: brighter for a project
with more stargazers, lit once merged, steady while in review, and a hollow ring
once closed. It uses galaxy-profile's stars, type and motion, so it reads as one
more plate of the same set.
"""

from __future__ import annotations

from generator.motion import Motion
from generator.svg import frame, star, star_defs
from generator.typeset import Typesetter, measure, wrap

# pull request state -> (star state, word shown)
STATES = {"merged": ("now", "merged"), "open": ("year", "in review"), "closed": ("dorm", "closed")}
CAPTION = "pull requests to open-source projects"
EMPTY = "No pull requests to show yet"
STAR_SCALE = 0.5        # the stars sit close together in one column


def _stargazers(count: int) -> str:
    if count >= 10_000:
        return f"{count // 1000}k stars"
    if count >= 1000:
        return f"{count / 1000:.1f}".rstrip("0").rstrip(".") + "k stars"
    return f"{count} star{'' if count == 1 else 's'}"


def _header(pulls, theme, ts, mo, width, margin, mobile) -> tuple[list, float]:
    """The figure, its caption and (on wide plates) the counters. Returns the parts and the first row's top."""
    parts = []
    size, title_y = (34, 50) if mobile else (44, 58)
    figure = str(len(pulls))
    parts.append(ts.line(margin, title_y, figure, size, theme.ink, "light", attrs=mo.cls("soft", delay=0.1)))
    caption_x = margin + measure(figure, size, "light") + 10
    caption_size = 15 if mobile else 17
    lines = wrap(CAPTION, caption_size, "italic", width - margin - caption_x, max_lines=2)
    for j, line in enumerate(lines):
        parts.append(ts.line(caption_x, title_y + j * 20, line, caption_size, theme.mute, "italic",
                             attrs=mo.cls("soft", delay=0.2)))
    if not mobile:
        counters = [(str(sum(pr.state == "open" for pr in pulls)), "in review"),
                    (str(sum(pr.state == "merged" for pr in pulls)), "merged")]
        x = width - margin
        for value, label in counters:
            parts.append(ts.line(x, 42, value, 22, theme.ink, "regular", anchor="end", attrs=mo.cls("soft", delay=0.3)))
            parts.append(ts.line(x, 60, label, 13, theme.mute, "italic", anchor="end", attrs=mo.cls("soft", delay=0.3)))
            x -= max(measure(value, 22), measure(label, 13, "italic")) + 28
    return parts, title_y + 20 * (len(lines) - 1) + (30 if mobile else 38)


def render(pulls: list, theme, mobile: bool = False, motion: bool = True) -> str:
    """pulls are extras.pulls.PullRequest, newest first."""
    mo, ts = Motion(motion), Typesetter()
    width, margin = (390, 24) if mobile else (850, 44)
    if not pulls:
        body = ts.line(margin, 62, EMPTY, 16, theme.mute, "italic")
        return frame(theme, width, 110, body, "Open source", EMPTY, ts.defs(), mo)

    body, top = _header(pulls, theme, ts, mo, width, margin, mobile)
    stars = []
    step = 96 if mobile else 58
    for k, pr in enumerate(pulls):
        state, word = STATES.get(pr.state, STATES["open"])
        row = top + k * step
        delay = 0.35 + k * 0.12
        gx, gy = margin + (10 if mobile else 12), row + 15
        tx = margin + (34 if mobile else 46)
        stars.append(f'<g transform="translate({gx} {gy})"><g{mo.cls("pop", delay=delay)}>'
                     f'{star(pr.stars, state, theme, mo, phase=k * 0.9, scale=STAR_SCALE)}</g></g>')
        word_fill = theme.now if pr.state == "merged" else theme.ink if pr.state == "open" else theme.mute
        text = mo.cls("soft", delay=delay + 0.1)
        if mobile:
            limit = width - margin - tx
            name = wrap(pr.repo, 16, "medium", limit, max_lines=1)[0]
            title = wrap(pr.title, 14, "italic", limit, max_lines=2)
            body.append(ts.line(tx, row + 20, name, 16, theme.ink, "medium", attrs=text))
            for j, line in enumerate(title):
                body.append(ts.line(tx, row + 41 + j * 18, line, 14, theme.mute, "italic", attrs=text))
            meta_y = row + 43 + len(title) * 18
            body.append(ts.line(tx, meta_y, word, 13, word_fill, "italic", attrs=text))
            body.append(ts.line(tx + measure(word, 13, "italic") + 8, meta_y,
                                f"#{pr.number}  ·  {_stargazers(pr.stars)}", 12.5, theme.mute, attrs=text))
            continue
        right = width - margin
        limit = right - 140 - tx
        name = wrap(pr.repo, 18, "medium", limit * 0.62, max_lines=1)[0]
        body.append(ts.line(tx, row + 21, name, 18, theme.ink, "medium", attrs=text))
        body.append(ts.line(tx + measure(name, 18, "medium") + 10, row + 21, _stargazers(pr.stars), 13.5,
                            theme.mute, "italic", attrs=text))
        body.append(ts.line(tx, row + 43, wrap(pr.title, 14.5, "italic", limit, max_lines=1)[0], 14.5, theme.mute,
                            "italic", attrs=text))
        body.append(ts.line(right, row + 21, word, 15, word_fill, "italic", anchor="end", attrs=text))
        body.append(ts.line(right, row + 43, f"#{pr.number}", 13, theme.mute, anchor="end", attrs=text))
        if k < len(pulls) - 1:
            body.append(f'<path d="M{tx} {row + step - 6}H{right}" stroke="{theme.faint}" stroke-width=".8" '
                        f'stroke-opacity=".6"{mo.cls("soft", delay=delay + 0.2)}/>')

    height = top + len(pulls) * step + (4 if mobile else 6)
    desc = ". ".join(f"{pr.repo}: {pr.title}, {STATES.get(pr.state, STATES['open'])[1]}" for pr in pulls) + "."
    defs = star_defs(theme) + ts.defs()
    return frame(theme, width, round(height), "".join(stars + body), "Open source", desc, defs, mo)
