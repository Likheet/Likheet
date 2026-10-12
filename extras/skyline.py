"""The last year of contributions as a 3D skyline, written as a binary STL file.

GitHub shows .stl files in an interactive 3D viewer, but only up to 10 MB, and
the official gh-skyline extension writes models of about 25 MB. This model has
one block per active day on a plinth, a few thousand triangles, so it loads at once.
"""

from __future__ import annotations

import math
import struct

import requests

QUERY = """query($login: String!) {
  user(login: $login) {
    contributionsCollection { contributionCalendar { weeks { contributionDays { contributionCount weekday } } } }
  }
}"""

CELL = 2.0          # width of one day, in model units
GAP = 0.4           # space between neighbouring blocks
TALLEST = 30.0      # height of the busiest day
LOWEST = 1.2        # height of a day with one contribution
PLINTH = 3.0        # depth of the base under the blocks
MARGIN = 3.0        # base beyond the outer blocks


def fetch_weeks(login: str, token: str, http=requests) -> list:
    """Weeks of seven daily counts, Sunday first. Days outside the calendar count as 0."""
    response = http.post("https://api.github.com/graphql", json={"query": QUERY, "variables": {"login": login}},
                         headers={"Authorization": f"Bearer {token}", "User-Agent": f"{login}-profile"}, timeout=20)
    response.raise_for_status()
    body = response.json()
    if body.get("errors"):
        raise RuntimeError("; ".join(error["message"] for error in body["errors"]))
    weeks = []
    for week in body["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
        counts = [0] * 7
        for day in week["contributionDays"]:
            counts[day["weekday"]] = day["contributionCount"]
        weeks.append(counts)
    return weeks


def _box(x0, y0, z0, x1, y1, z1) -> list:
    """Twelve triangles (normal, three corners) with outward normals and counter-clockwise corners."""
    p = {(i, j, k): (x1 if i else x0, y1 if j else y0, z1 if k else z0)
         for i in (0, 1) for j in (0, 1) for k in (0, 1)}
    faces = [((0, 0, -1), (0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)),
             ((0, 0, 1), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)),
             ((0, -1, 0), (0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)),
             ((0, 1, 0), (0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)),
             ((-1, 0, 0), (0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)),
             ((1, 0, 0), (1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1))]
    triangles = []
    for normal, a, b, c, d in faces:
        triangles.append((normal, p[a], p[b], p[c]))
        triangles.append((normal, p[a], p[c], p[d]))
    return triangles


def build(weeks: list) -> list:
    """The triangles of the plinth and of one block per day with contributions."""
    width, depth = len(weeks) * CELL, 7 * CELL
    triangles = _box(-MARGIN, -MARGIN, -PLINTH, width - GAP + MARGIN, depth - GAP + MARGIN, 0)
    busiest = max((count for week in weeks for count in week), default=0) or 1
    for i, week in enumerate(weeks):
        for weekday, count in enumerate(week):
            if count:
                # Square root, so that quiet days still show next to the busiest ones.
                height = LOWEST + (TALLEST - LOWEST) * math.sqrt(count / busiest)
                x0, y0 = i * CELL, (6 - weekday) * CELL     # Sunday at the back, as on the GitHub graph
                triangles += _box(x0, y0, 0, x0 + CELL - GAP, y0 + CELL - GAP, height)
    return triangles


def to_stl(triangles: list, title: str) -> bytes:
    # A binary STL header must not start with "solid", which marks the text format.
    header = title.encode("ascii", "replace")[:80].ljust(80, b" ")
    parts = [header, struct.pack("<I", len(triangles))]
    for normal, a, b, c in triangles:
        parts.append(struct.pack("<12fH", *normal, *a, *b, *c, 0))
    return b"".join(parts)
