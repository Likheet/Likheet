"""Fills in the generated parts of README.md from live GitHub data.

    GITHUB_TOKEN=$(gh auth token) python update.py

README.md is written by hand, except between pairs of markers such as
<!-- auto:projects --> and <!-- /auto:projects -->, which this script rewrites.
The workflow runs it every day and commits README.md when something changed.

It only shows what grows: all-time totals, projects and pull requests to
other people's projects. No dates, streaks or activity over time.
"""

from __future__ import annotations

import os
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

import requests
import yaml

ROOT = Path(__file__).resolve().parent
GRAPHQL = "https://api.github.com/graphql"

PROFILE = """query($login: String!, $prs: String!) {
  user(login: $login) {
    pullRequests { totalCount }
    contributionsCollection { contributionYears }
    repositories(ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false, first: 100,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      nodes {
        name description url homepageUrl stargazerCount isArchived
        primaryLanguage { name }
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } }
      }
    }
  }
  search(query: $prs, type: ISSUE, first: 100) {
    nodes { ... on PullRequest { title url state merged repository { nameWithOwner url stargazerCount isPrivate } } }
  }
}"""


def query(token: str, text: str, **variables) -> dict:
    """Raises on any error, so a failed run leaves README.md as it was."""
    response = requests.post(GRAPHQL, json={"query": text, "variables": variables}, timeout=30,
                             headers={"Authorization": f"Bearer {token}"})
    response.raise_for_status()
    answer = response.json()
    if answer.get("errors"):
        raise RuntimeError(answer["errors"])
    return answer["data"]


def contributions(token: str, login: str, years: list) -> int:
    """All-time contributions, the sum of the yearly totals GitHub shows on the profile."""
    fields = " ".join(f'y{y}: contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{y}-12-31T23:59:59Z") '
                      "{ contributionCalendar { totalContributions } }" for y in years)
    user = query(token, f"query($login: String!) {{ user(login: $login) {{ {fields} }} }}", login=login)["user"]
    return sum(year["contributionCalendar"]["totalContributions"] for year in user.values())


def esc(text: str) -> str:
    """Text that markdown shows as written, except that `code` stays code (pull request titles use it)."""
    parts = re.split(r"(`[^`]+`)", " ".join(text.split()))
    return "".join(part if k % 2 else re.sub(r"([\\*_\[\]<>#|])", r"\\\1", part) for k, part in enumerate(parts))


def stars(count: int) -> str:
    if count >= 10_000:
        return f"★ {count // 1000}k"
    if count >= 1000:
        return f"★ {count / 1000:.1f}".rstrip("0").rstrip(".") + "k"
    return f"★ {count}"


def website(url: str) -> str:
    """A link to a project's website, named after its host when the address is just the host."""
    parts = urlparse(url)
    host = parts.netloc.removeprefix("www.")
    name = host if parts.path in ("", "/") and not parts.query else "Website"
    return f"[{name}]({url})"


def render_stats(user: dict, total: int, cfg: dict) -> str:
    sizes = Counter()
    for repo in user["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            sizes[edge["node"]["name"]] += edge["size"]
    skipped = set(cfg.get("ignore_languages", []))
    top = [name for name, _ in sizes.most_common() if name not in skipped][:3]
    languages = ", ".join(top[:-1]) + f" and {top[-1]}" if len(top) > 1 else "".join(top)
    return (f"**{total:,}** contributions · **{user['pullRequests']['totalCount']:,}** pull requests · "
            f"**{user['repositories']['totalCount']}** public repositories  \n"
            f"Mostly {languages}")


def render_projects(user: dict, login: str, cfg: dict) -> str:
    skipped = {name.lower() for name in cfg.get("exclude", [])} | {login.lower()}
    repos = [repo for repo in user["repositories"]["nodes"]
             if repo["description"] and not repo["isArchived"] and repo["name"].lower() not in skipped]
    shown, rest = repos[:cfg.get("limit", 6)], repos[cfg.get("limit", 6):]

    blocks = []
    for item in cfg.get("first", []):
        meta = [f"**[{esc(item['name'])}]({item['url']})**"] + ([esc(item["note"])] if item.get("note") else [])
        blocks.append(" · ".join(meta) + f"  \n{esc(item['description'])}")
    for repo in shown:
        meta = [f"**[{esc(repo['name'])}]({repo['url']})**"]
        if repo["primaryLanguage"]:
            meta.append(repo["primaryLanguage"]["name"])
        if repo["stargazerCount"] >= cfg.get("show_stars_from", 1):
            meta.append(stars(repo["stargazerCount"]))
        if repo["homepageUrl"]:
            meta.append(website(repo["homepageUrl"]))
        blocks.append(" · ".join(meta) + f"  \n{esc(repo['description'])}")
    out = "\n\n".join(blocks)
    if rest:
        rest.sort(key=lambda repo: (-repo["stargazerCount"], repo["name"].lower()))
        lines = "\n".join(f"- [{esc(repo['name'])}]({repo['url']}): {esc(repo['description'])}" for repo in rest)
        out += f"\n\n<details>\n<summary>More projects</summary>\n\n{lines}\n\n</details>"
    return out


def render_open_source(pulls: list, login: str, cfg: dict) -> str:
    """Pull requests to other people's public projects, merged or in review, biggest project first."""
    skipped = {name.lower() for name in cfg.get("exclude", [])}
    projects = {}
    for pr in pulls:
        repo = pr.get("repository")
        if (not repo or repo["isPrivate"] or repo["nameWithOwner"].lower() in skipped
                or repo["stargazerCount"] < cfg.get("min_stars", 100) or (pr["state"] == "CLOSED" and not pr["merged"])):
            continue
        projects.setdefault(repo["nameWithOwner"], (repo, []))[1].append(pr)
    if not projects:
        return "Nothing here yet."

    ordered = sorted(projects.values(), key=lambda entry: -entry[0]["stargazerCount"])
    combined = sum(repo["stargazerCount"] for repo, _ in ordered)
    blocks = [f"Pull requests to projects with {stars(combined)[2:]} stars between them."]
    for repo, prs in ordered[:cfg.get("limit", 8)]:
        prs.sort(key=lambda pr: not pr["merged"])
        lines = [f"**[{esc(repo['nameWithOwner'])}]({repo['url']})** · {stars(repo['stargazerCount'])}"]
        lines += [f"[{esc(pr['title'])}]({pr['url']}) · {'merged' if pr['merged'] else 'in review'}"
                  for pr in prs[:2]]
        if len(prs) > 2:
            lines.append(f"and {len(prs) - 2} more")
        blocks.append("  \n".join(lines))
    if len(ordered) > cfg.get("limit", 8):
        blocks.append(f"[and {len(ordered) - cfg.get('limit', 8)} more projects]"
                      f"(https://github.com/search?q=is%3Apr+author%3A{login}+-user%3A{login}&type=pullrequests)")
    return "\n\n".join(blocks)


def fill(readme: str, name: str, body: str) -> str:
    pattern = re.compile(rf"(<!-- auto:{name} -->\n).*?(<!-- /auto:{name} -->)", re.S)
    if not pattern.search(readme):
        raise RuntimeError(f"README.md has no <!-- auto:{name} --> markers")
    return pattern.sub(lambda match: match.group(1) + body + "\n" + match.group(2), readme)


def main() -> None:
    cfg = yaml.safe_load((ROOT / "config.yml").read_text(encoding="utf-8"))
    login, token = cfg["username"], os.environ["GITHUB_TOKEN"]
    data = query(token, PROFILE, login=login, prs=f"is:pr author:{login} -user:{login}")
    user = data["user"]
    total = contributions(token, login, user["contributionsCollection"]["contributionYears"])

    path = ROOT / "README.md"
    readme = path.read_text(encoding="utf-8")
    readme = fill(readme, "stats", render_stats(user, total, cfg.get("stats", {})))
    readme = fill(readme, "projects", render_projects(user, login, cfg.get("projects", {})))
    readme = fill(readme, "open-source", render_open_source(data["search"]["nodes"], login, cfg.get("open_source", {})))
    path.write_text(readme, encoding="utf-8")


if __name__ == "__main__":
    main()
