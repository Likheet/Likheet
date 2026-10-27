"""Draws the profile's images from live GitHub data into OUT_DIR (default: dist).

    GITHUB_TOKEN=$(gh auth token) python build.py

The workflow runs it every hour and on every push to main, and publishes the
images to the `images` branch, where README.md points. README.md itself
never changes. Any error stops the build, so the images of the last good run
stay online.
"""

from __future__ import annotations

import base64
import os
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import requests
import yaml
from PIL import Image

from art import cards, dither

ROOT = Path(__file__).resolve().parent
GRAPHQL = "https://api.github.com/graphql"

QUERY = """query($login: String!, $prs: String!) {
  user(login: $login) {
    createdAt
    avatarUrl
    pullRequests { totalCount }
    contributionsCollection { contributionYears }
    repositories(ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false, first: 100,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      nodes {
        name description stargazerCount isArchived primaryLanguage { name }
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } }
      }
    }
  }
  search(query: $prs, type: ISSUE, first: 100) {
    nodes { ... on PullRequest { title repository { name owner { login avatarUrl } stargazerCount isPrivate } } }
  }
}"""


@dataclass(frozen=True)
class Project:
    name: str
    description: str
    language: str = ""
    stars: int = 0
    note: str = ""          # for a project from config.yml, e.g. "Public beta"
    link: str = ""


@dataclass(frozen=True)
class Contribution:
    owner: str
    name: str
    stars: int
    merged: int             # my pull requests merged into it
    title: str              # the newest of them
    avatar: str             # the owner's avatar, as a data URI


@dataclass(frozen=True)
class Profile:
    name: str
    handle: str             # the user@host line of the card
    builds: str
    studying: str
    uptime: str             # time since joining GitHub
    avatar: Image.Image
    contributions: int      # all time, as the yearly totals on the profile
    pull_requests: int
    repositories: int
    stars: int              # stargazers of my public repositories
    merged: int             # my pull requests merged into other people's projects
    languages: list         # the three with the most code
    projects: list
    open_source: list


def query(token: str, text: str, **variables) -> dict:
    response = requests.post(GRAPHQL, json={"query": text, "variables": variables}, timeout=30,
                             headers={"Authorization": f"Bearer {token}"})
    response.raise_for_status()
    answer = response.json()
    if answer.get("errors"):
        raise RuntimeError(answer["errors"])
    return answer["data"]


def contributions(token: str, login: str, years: list) -> int:
    fields = " ".join(f'y{y}: contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{y}-12-31T23:59:59Z") '
                      "{ contributionCalendar { totalContributions } }" for y in years)
    user = query(token, f"query($login: String!) {{ user(login: $login) {{ {fields} }} }}", login=login)["user"]
    return sum(year["contributionCalendar"]["totalContributions"] for year in user.values())


def pick_projects(repos: list, login: str, cfg: dict) -> list:
    """The projects in config.yml, then my most recently pushed public repositories that have a description."""
    skipped = {name.lower() for name in cfg.get("exclude", [])} | {login.lower()}
    chosen = [Project(item["name"], item.get("description", ""), note=item.get("note", ""), link=item.get("link", ""))
              for item in cfg.get("first", [])]
    for repo in repos:
        if len(chosen) >= len(cfg.get("first", [])) + cfg.get("limit", 5):
            break
        if repo["description"] and not repo["isArchived"] and repo["name"].lower() not in skipped:
            stars = repo["stargazerCount"] if repo["stargazerCount"] >= cfg.get("show_stars_from", 1) else 0
            language = (repo["primaryLanguage"] or {}).get("name", "")
            chosen.append(Project(repo["name"], repo["description"], language, stars))
    return chosen


def data_uri(url: str, size: int = 40) -> str:
    response = requests.get(url, params={"s": size}, timeout=30)
    response.raise_for_status()
    kind = response.headers.get("content-type", "image/png").split(";")[0]
    return f"data:{kind};base64,{base64.b64encode(response.content).decode()}"


def pick_open_source(pulls: list, cfg: dict) -> list:
    """Other people's public projects that merged my pull requests, biggest first. `pulls` is newest first."""
    skipped = {name.lower() for name in cfg.get("exclude", [])}
    found = {}
    for pr in pulls:
        repo = pr.get("repository")
        if not repo or repo["isPrivate"]:
            continue
        full = f"{repo['owner']['login']}/{repo['name']}"
        if full.lower() in skipped or repo["stargazerCount"] < cfg.get("min_stars", 100):
            continue
        count, title, _ = found.get(full, (0, pr["title"], repo))
        found[full] = (count + 1, title, repo)
    chosen = sorted(found.values(), key=lambda entry: -entry[2]["stargazerCount"])[:cfg.get("limit", 8)]
    return [Contribution(repo["owner"]["login"], repo["name"], repo["stargazerCount"], count, title,
                         data_uri(repo["owner"]["avatarUrl"]))
            for count, title, repo in chosen]


def uptime(joined: date, today: date) -> str:
    months = (today.year - joined.year) * 12 + today.month - joined.month - (today.day < joined.day)
    years, months = divmod(months, 12)
    parts = [f"{years} year{'s' * (years != 1)}"] if years else []
    if months:
        parts.append(f"{months} month{'s' * (months != 1)}")
    return ", ".join(parts) or "new"


def top_languages(repos: list, ignore: list) -> list:
    sizes = Counter()
    for repo in repos:
        for edge in repo["languages"]["edges"]:
            sizes[edge["node"]["name"]] += edge["size"]
    return [name for name, _ in sizes.most_common() if name not in ignore][:3]


def fetch(cfg: dict, token: str) -> Profile:
    login = cfg["username"]
    data = query(token, QUERY, login=login, prs=f"is:pr is:merged author:{login} -user:{login} sort:created-desc")
    user = data["user"]
    repos = user["repositories"]["nodes"]
    found = pick_open_source(data["search"]["nodes"], cfg.get("open_source", {}))
    return Profile(
        name=cfg["name"], handle=cfg["handle"], builds=cfg["builds"], studying=cfg["studying"],
        uptime=uptime(date.fromisoformat(user["createdAt"][:10]), date.today()),
        avatar=dither.avatar(user["avatarUrl"]),
        contributions=contributions(token, login, user["contributionsCollection"]["contributionYears"]),
        pull_requests=user["pullRequests"]["totalCount"],
        repositories=user["repositories"]["totalCount"],
        stars=sum(repo["stargazerCount"] for repo in repos),
        merged=sum(c.merged for c in found),
        languages=top_languages(repos, cfg.get("ignore_languages", [])),
        projects=pick_projects(repos, login, cfg.get("projects", {})),
        open_source=found,
    )


def main() -> None:
    cfg = yaml.safe_load((ROOT / "config.yml").read_text(encoding="utf-8"))
    profile = fetch(cfg, os.environ["GITHUB_TOKEN"])
    out = Path(os.environ.get("OUT_DIR", "dist"))
    out.mkdir(parents=True, exist_ok=True)
    for name, draw in (("hero", cards.hero), ("work", cards.work)):
        for theme in ("dark", "light"):
            for mobile in (False, True):
                suffix = ("-mobile" if mobile else "") + ("-light" if theme == "light" else "")
                (out / f"{name}{suffix}.svg").write_text(draw(profile, theme, mobile), encoding="utf-8")
    print(f"Drew {len(profile.projects)} projects and {len(profile.open_source)} open-source projects into {out}/")


if __name__ == "__main__":
    main()
