"""The two cards of the profile: who I am (hero) and what I work on (work).

Built from the best profiles I found: the terminal "neofetch" card from Andrew6rant, the
dithered portrait from 0xharkirat's dither-portrait, one self-contained card from terkelg,
and self-updating lists from simonw and tw93. Each card comes in dark and light, wide (850 px)
and for phones (390 px), and only shows what grows: no dates, nothing over time.
"""

from __future__ import annotations

import math

from art import dither
from art.svg import esc, num
from art.type import ADVANCE, Typesetter, clause, first_sentence, fit

THEMES = {
    "dark": {"bg": "#161b22", "line": "#30363d", "text": "#e6edf3", "muted": "#7d8590", "key": "#ff8f73",
             "merged": "#a371f7", "shadow": "#4b3f73", "banner": ("#8f6fd0", "#e0607a", "#ff9a78", "#ffd2b8")},
    "light": {"bg": "#f6f8fa", "line": "#d0d7de", "text": "#1f2328", "muted": "#6e7781", "key": "#c44b62",
              "merged": "#8250df", "shadow": "#c9bfe3", "banner": ("#5b45a8", "#c44b62", "#e5604f", "#f08a5d")},
}
CURSOR = ".cur{animation:cur 1.1s step-end infinite}@keyframes cur{50%{opacity:0}}"

# GitHub's colours for languages (github-linguist)
LANGUAGES = {"TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Python": "#3572A5", "Rust": "#dea584",
             "Swift": "#F05138", "Kotlin": "#A97BFF", "C++": "#f34b7d", "Go": "#00ADD8", "Java": "#b07219",
             "HTML": "#e34c26", "CSS": "#663399", "Shell": "#89e051", "Astro": "#ff5a03",
             "Jupyter Notebook": "#DA5B0B"}

# The letters of the name in the "ANSI Shadow" figlet style: solid blocks with a box-drawn shadow.
FIGLET = {
    "E": ["███████╗", "██╔════╝", "█████╗  ", "██╔══╝  ", "███████╗", "╚══════╝"],
    "H": ["██╗  ██╗", "██║  ██║", "███████║", "██╔══██║", "██║  ██║", "╚═╝  ╚═╝"],
    "I": ["██╗", "██║", "██║", "██║", "██║", "╚═╝"],
    "K": ["██╗  ██╗", "██║ ██╔╝", "█████╔╝ ", "██╔═██╗ ", "██║  ██╗", "╚═╝  ╚═╝"],
    "L": ["██╗     ", "██║     ", "██║     ", "██║     ", "███████╗", "╚══════╝"],
    "T": ["████████╗", "╚══██╔══╝", "   ██║   ", "   ██║   ", "   ██║   ", "   ╚═╝   "],
}


def short(count: int) -> str:
    if count >= 10_000:
        return f"{count // 1000}k"
    if count >= 1000:
        return f"{count / 1000:.1f}".rstrip("0").rstrip(".") + "k"
    return str(count)


def _svg(width: int, height: int, theme: dict, body: str, defs: str, css: str, title: str, desc: str) -> str:
    style = f"<style>@media (prefers-reduced-motion:no-preference){{{css}}}</style>" if css else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" '
            f'height="{height}" role="img" aria-labelledby="t d"><title id="t">{esc(title)}</title>'
            f'<desc id="d">{esc(desc)}</desc><defs>{defs}{style}</defs>'
            f'<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="12" fill="{theme["bg"]}" '
            f'stroke="{theme["line"]}"/>{body}</svg>')


def _star(x: float, y: float, size: float, fill: str) -> str:
    """A five-pointed star filling the character cell at x (the font has no ★)."""
    cx, cy, r = x + size * ADVANCE / 2, y - size * .36, size * .34
    points = []
    for k in range(10):
        angle = -math.pi / 2 + k * math.pi / 5
        reach = r if k % 2 == 0 else r * .45
        points.append(f"{num(cx + math.cos(angle) * reach)} {num(cy + math.sin(angle) * reach)}")
    return f'<path d="M{"L".join(points)}Z" fill="{fill}"/>'


def _merge(x: float, y: float, size: float, colour: str) -> str:
    """A merged-branch mark (two commits joined by a curve, after Lucide's git-merge) in the cell at x."""
    s = size / 24 * 1.15
    return (f'<g transform="translate({num(x + size * ADVANCE / 2 - 12 * s)} {num(y - size * .82)}) scale({num(s, 3)})" '
            f'fill="none" stroke="{colour}" stroke-width="2.4" stroke-linecap="round">'
            f'<circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M6 21V9a9 9 0 0 0 9 9"/></g>')


class Screen:
    """A terminal screen: text on a grid of `cols` character cells from (x, y), one row per call."""

    def __init__(self, ts: Typesetter, theme: dict, x: float, y: float, size: float, leading: float,
                 cols: int) -> None:
        self.ts, self.theme, self.x, self.y = ts, theme, x, y
        self.size, self.leading, self.cols = size, leading, cols
        self.cell = size * ADVANCE
        self.parts: list = []
        self.defs: list = []

    def put(self, col: float, text: str, colour: str, bold: bool = False) -> None:
        """Text at column `col` of the current row; ★ is drawn as a star and ⇄ as a merge mark."""
        x = self.x + col * self.cell
        self.parts.append(self.ts.line(x, self.y, text.replace("⇄", " "), self.size, colour, bold))
        for k, ch in enumerate(text):
            if ch == "★":
                self.parts.append(_star(x + k * self.cell, self.y, self.size, colour))
            elif ch == "⇄":
                self.parts.append(_merge(x + k * self.cell, self.y, self.size, self.theme["merged"]))

    def pair(self, key: str, value: str, col: int = 0, width: int = 0) -> None:
        """key ······ value, the value flush right in `width` cells; a long value goes on its own row."""
        width = width or self.cols - col
        self.put(col, key, self.theme["key"], bold=True)
        if len(value) > width - len(key) - 3:
            self.down()
            value = fit(value, width)
        else:
            self.put(col + len(key) + 1, "·" * (width - len(key) - len(value) - 2), self.theme["muted"])
        self.put(col + width - len(value), value, self.theme["text"])

    def dot(self, col: float, colour: str) -> None:
        cx = self.x + (col + .5) * self.cell
        self.parts.append(f'<circle cx="{num(cx)}" cy="{num(self.y - self.size * .33)}" r="{num(self.size * .3)}" '
                          f'fill="{colour}"/>')

    def image(self, col: float, uri: str) -> None:
        """A small rounded square image (a project's logo) in the cell at col."""
        side = self.size * 1.1
        x, y = self.x + col * self.cell + (self.cell - side) / 2, self.y - self.size * .86
        cid = f"logo{len(self.defs)}"
        self.defs.append(f'<clipPath id="{cid}"><rect x="{num(x)}" y="{num(y)}" width="{num(side)}" '
                         f'height="{num(side)}" rx="{num(side * .22)}"/></clipPath>')
        self.parts.append(f'<image href="{uri}" x="{num(x)}" y="{num(y)}" width="{num(side)}" height="{num(side)}" '
                          f'clip-path="url(#{cid})"/>')

    def cursor(self, col: int) -> None:
        x = self.x + col * self.cell
        self.parts.append(f'<rect class="cur" x="{num(x)}" y="{num(self.y - self.size * .78)}" '
                          f'width="{num(self.cell)}" height="{num(self.size * .95)}" fill="{self.theme["key"]}"/>')

    def down(self, rows: float = 1) -> None:
        self.y += self.leading * rows


def _banner(ts: Typesetter, theme: dict, word: str, x: float, top: float, size: float) -> tuple:
    """(defs, markup, css, height) for the word in figlet letters: sunset-coloured blocks over a
    lilac shadow, with a glint of light crossing it now and then.

    The blocks are one path, so the gradient runs across the whole word and no seams show between
    neighbouring blocks.
    """
    rows = ["".join(FIGLET[ch][r] for ch in word.upper()) for r in range(6)]
    cell, width = size * ADVANCE, len(rows[0]) * size * ADVANCE
    stops = "".join(f'<stop offset="{num(k / (len(theme["banner"]) - 1), 2)}" stop-color="{c}"/>'
                    for k, c in enumerate(theme["banner"]))
    blocks, shadow = [], []
    for r, row in enumerate(rows):
        c = 0
        while c < len(row):
            if row[c] == "█":
                end = c
                while end < len(row) and row[end] == "█":
                    end += 1
                blocks.append(f"M{num(x + c * cell)} {num(top + r * size)}h{num((end - c) * cell)}v{num(size)}"
                              f"h{num(-(end - c) * cell)}Z")
                c = end
            else:
                c += 1
        shade = "".join(ch if ch not in "█ " else " " for ch in row)
        shadow.append(ts.line(x, top + size * (r + .8), shade, size, theme["shadow"], bold=True))
    shape = "".join(blocks)
    glint_w = width * .22
    defs = (f'<linearGradient id="sunset" gradientUnits="userSpaceOnUse" x1="{num(x)}" y1="0" '
            f'x2="{num(x + width)}" y2="0">{stops}</linearGradient>'
            f'<linearGradient id="glint"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
            f'<stop offset=".5" stop-color="#fff" stop-opacity=".55"/>'
            f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
            f'<mask id="word"><path d="{shape}" fill="#fff"/></mask>')
    css = (f".glint{{animation:glint 7s ease-in-out 1.5s infinite}}"
           f"@keyframes glint{{0%{{transform:translateX(0)}}25%,100%{{transform:translateX({num(width + glint_w)}px)}}}}")
    markup = ("".join(shadow) + f'<path d="{shape}" fill="url(#sunset)"/>'
              f'<g mask="url(#word)"><rect class="glint" x="{num(x - glint_w)}" y="{num(top)}" '
              f'width="{num(glint_w)}" height="{num(size * 6)}" fill="url(#glint)"/></g>')
    return defs, markup, css, size * 6


def hero(profile, theme_name: str = "dark", mobile: bool = False) -> str:
    """The avatar as a rippling dither; beside it the name in figlet letters and the facts, as neofetch prints them."""
    theme, ts = THEMES[theme_name], Typesetter()
    word = profile.name.split()[0]
    letters = len("".join(FIGLET[ch][0] for ch in word.upper()))
    if mobile:
        width, pad, picture, size, leading = 390, 20, 350, 12.5, 21
        px, py = pad, pad
        sx, top = pad, pad + picture + 26
        cols = int((width - 2 * pad) / (size * ADVANCE))
        banner_size = (width - 2 * pad) / letters / ADVANCE
    else:
        width, pad, picture, size, leading = 850, 28, 320, 13.5, 23
        px, py = pad, pad
        sx, top = pad + picture + 34, pad + 6
        cols = int((width - pad - sx) / (size * ADVANCE))
        banner_size = min(11.5, (width - pad - sx) / letters / ADVANCE)
    banner_defs, banner, banner_css, banner_h = _banner(ts, theme, word, sx, top, banner_size)

    screen = Screen(ts, theme, sx, top + banner_h + 26, size, leading, cols)
    screen.put(0, profile.builds.replace(", ", " · "), theme["muted"])
    screen.cursor(len(profile.builds.replace(", ", " · ")) + 1)
    screen.down(1.1)
    screen.put(0, "─" * cols, theme["line"])
    screen.down()
    room, names = cols - len("Merged into") - 3, []
    for k, c in enumerate(profile.open_source):
        rest = len(profile.open_source) - k - 1
        if len(" · ".join(names + [c.name])) + (len(f" +{rest}") if rest else 0) > room:
            break
        names.append(c.name)
    merged_into = " · ".join(names) + (f" +{len(profile.open_source) - len(names)}"
                                       if len(names) < len(profile.open_source) else "")
    for key, value in (("Uptime", profile.uptime), ("Shipping", " · ".join(p.name for p in profile.projects[:2])),
                       ("Studying", profile.studying), ("Languages", " · ".join(profile.languages)),
                       ("Merged into", merged_into)):
        screen.pair(key, value)
        screen.down()
    screen.put(0, "─" * cols, theme["line"])
    screen.down()
    stats = [("Contributions", f"{profile.contributions:,}"), ("Pull requests", f"{profile.pull_requests:,}"),
             ("Merged upstream", str(profile.merged)), ("Projects", str(profile.repositories))]
    if mobile:
        for key, value in stats:
            screen.pair(key, value)
            screen.down()
    else:
        half = (cols - 3) // 2
        for left, right in ((stats[0], stats[1]), (stats[2], stats[3])):
            screen.pair(*left, width=half)
            screen.pair(*right, col=cols - half, width=half)
            screen.down()
    screen.down(.35)
    for k, colour in enumerate(dither.PALETTE):
        screen.put(k * 3, "███", colour)
    height = round(max(py + picture, screen.y) + pad)

    art_css, art = dither.svg(dither.dither(profile.avatar, 88 if mobile else 84), picture)
    portrait = (f'<clipPath id="pic"><rect width="{picture}" height="{picture}" rx="10"/></clipPath>',
                f'<g transform="translate({px} {py})"><g clip-path="url(#pic)">{art}</g></g>')
    desc = (f"{profile.name}: {profile.builds}. Shipping {', '.join(p.name for p in profile.projects[:2])}. "
            f"Merged pull requests into {', '.join(c.name for c in profile.open_source)}. "
            + ". ".join(f"{key}: {value}" for key, value in stats)
            + ". Beside it, my profile picture, a figure on a rock above sunset clouds, drawn in coloured dots.")
    return _svg(width, height, theme, portrait[1] + banner + "".join(screen.parts),
                portrait[0] + banner_defs + ts.defs(), art_css + banner_css + CURSOR, profile.name, desc)


def work(profile, theme_name: str = "dark", mobile: bool = False) -> str:
    """Projects, and pull requests merged into other people's projects, listed as a terminal would."""
    theme, ts = THEMES[theme_name], Typesetter()
    if mobile:
        width, pad, size, leading = 390, 20, 12, 20
    else:
        width, pad, size, leading = 850, 28, 13, 23
    cols = int((width - 2 * pad) / (size * ADVANCE))
    screen = Screen(ts, theme, pad, pad + 16, size, leading, cols)

    def prompt(command: str) -> None:
        screen.put(0, "$", theme["key"], bold=True)
        screen.put(2, command, theme["text"])
        screen.down()

    def row(name: str, about: str, meta: str, meta_colour: str, mark=None) -> None:
        """mark draws the little thing before the name: a language dot or a project's logo."""
        lead = 2 if mark else 0
        if mark:
            mark(0)
        if mobile:
            screen.put(lead, fit(name, cols - len(meta) - lead - 2), theme["text"], bold=True)
            screen.put(cols - len(meta), meta, meta_colour)
            screen.down()
            screen.put(lead, clause(about, cols - lead), theme["muted"])
        else:
            name_w = 22
            screen.put(lead, fit(name, name_w - lead - 1), theme["text"], bold=True)
            screen.put(name_w, clause(about, cols - name_w - len(meta) - 3), theme["muted"])
            screen.put(cols - len(meta), meta, meta_colour)
        screen.down()

    prompt("ls ~/projects")
    for p in profile.projects:
        if p.note:
            meta, colour = p.note.lower(), theme["key"]
        else:
            meta = " ".join(filter(None, [p.language, f"★{short(p.stars)}" if p.stars else ""]))
            colour = theme["muted"]
        dot = LANGUAGES.get(p.language, theme["key"] if p.note else theme["muted"])
        row(p.name, first_sentence(p.description), meta, colour, lambda col, c=dot: screen.dot(col, c))
    screen.down(.6)
    prompt("gh pr list --author @me --merged")
    for c in profile.open_source:
        meta = f"⇄ {c.merged} merged · ★{short(c.stars)}"
        row(c.name, c.title, meta, theme["muted"], lambda col, uri=c.avatar: screen.image(col, uri))
    screen.down(.6)
    screen.put(0, "$", theme["key"], bold=True)
    screen.cursor(2)
    height = round(screen.y + pad - leading + 8)

    desc = (" ".join(f"{p.name}: {p.description}" for p in profile.projects) + " Merged pull requests: "
            + " ".join(f"{c.owner}/{c.name} ({short(c.stars)} stars), {c.merged} merged, newest: {c.title}."
                       for c in profile.open_source))
    return _svg(width, height, theme, "".join(screen.parts), "".join(screen.defs) + ts.defs(), CURSOR,
                "Projects and open source", desc)
