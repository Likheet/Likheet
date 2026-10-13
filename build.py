"""Draws the profile's images from live GitHub data into OUT_DIR (default: dist).

    GITHUB_TOKEN=$(gh auth token) python build.py

The workflow runs it every day and on every push to main, and publishes the
images to the `images` branch, where README.md points. README.md itself
never changes. Any error stops the build, so the images of the last good run
stay online.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import requests
import yaml

from art import plates

ROOT = Path(__file__).resolve().parent
GRAPHQL = "https://api.github.com/graphql"

QUERY = """query($login: String!, $prs: String!) {
  user(login: $login) {
    pullRequests { totalCount }
    contributionsCollection { contributionYears }
    repositories(ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false, first: 100,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      nodes { name description stargazerCount isArchived primaryLanguage { name } }
    }
  }
  search(query: $prs, type: ISSUE, first: 100) {
    nodes { ... on PullRequest { state merged repository { name owner { login } stargazerCount isPrivate } } }
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
    merged: bool            # at least one pull request merged
    open: bool              # at least one still in review


@dataclass(frozen=True)
class Profile:
    name: str
    tagline: str
    contributions: int      # all time, as the yearly totals on the profile
    pull_requests: int
    repositories: int
    projects: list
    open_source: list
    open_source_stars: int


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


def pick_open_source(pulls: list, cfg: dict) -> list:
    """Other people's public projects I opened pull requests to, merged or in review, biggest first."""
    skipped = {name.lower() for name in cfg.get("exclude", [])}
    found = {}
    for pr in pulls:
        repo = pr.get("repository")
        if not repo or repo["isPrivate"] or (pr["state"] == "CLOSED" and not pr["merged"]):
            continue
        full = f"{repo['owner']['login']}/{repo['name']}"
        if full.lower() in skipped or repo["stargazerCount"] < cfg.get("min_stars", 100):
            continue
        merged, still_open, _ = found.get(full, (False, False, repo))
        found[full] = (merged or pr["merged"], still_open or pr["state"] == "OPEN", repo)
    out = [Contribution(repo["owner"]["login"], repo["name"], repo["stargazerCount"], merged, still_open)
           for merged, still_open, repo in found.values()]
    out.sort(key=lambda c: -c.stars)
    return out[:cfg.get("limit", 8)]


def fetch(cfg: dict, token: str) -> Profile:
    login = cfg["username"]
    data = query(token, QUERY, login=login, prs=f"is:pr author:{login} -user:{login}")
    user = data["user"]
    found = pick_open_source(data["search"]["nodes"], cfg.get("open_source", {}))
    return Profile(
        name=cfg["name"], tagline=cfg["tagline"],
        contributions=contributions(token, login, user["contributionsCollection"]["contributionYears"]),
        pull_requests=user["pullRequests"]["totalCount"],
        repositories=user["repositories"]["totalCount"],
        projects=pick_projects(user["repositories"]["nodes"], login, cfg.get("projects", {})),
        open_source=found,
        open_source_stars=sum(c.stars for c in found),
    )


def main() -> None:
    cfg = yaml.safe_load((ROOT / "config.yml").read_text(encoding="utf-8"))
    profile = fetch(cfg, os.environ["GITHUB_TOKEN"])
    out = Path(os.environ.get("OUT_DIR", "dist"))
    out.mkdir(parents=True, exist_ok=True)
    for name, draw in (("header", plates.header), ("projects", plates.projects), ("open-source", plates.open_source)):
        (out / f"{name}.svg").write_text(draw(profile), encoding="utf-8")
        (out / f"{name}-mobile.svg").write_text(draw(profile, mobile=True), encoding="utf-8")
    print(f"Drew {len(profile.projects)} projects and {len(profile.open_source)} open-source projects into {out}/")


if __name__ == "__main__":
    main()
