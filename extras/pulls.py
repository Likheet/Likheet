"""Pull requests to other people's public projects, with each project's stargazers."""

from __future__ import annotations

from dataclasses import dataclass

import requests

API = "https://api.github.com"


@dataclass(frozen=True)
class PullRequest:
    repo: str        # owner/name
    title: str
    number: int
    state: str       # "merged", "open" or "closed"
    stars: int       # stargazers of the project, not of the pull request


def fetch(login: str, token: str, min_stars: int, exclude: list, limit: int, http=requests) -> list:
    """The newest pull requests to public projects with at least min_stars stargazers.

    Raises on any network or API error, so a failed run keeps the last good image.
    """
    headers = {"Accept": "application/vnd.github+json", "User-Agent": f"{login}-profile"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    def get(path: str, **params) -> dict:
        response = http.get(f"{API}{path}", params=params, headers=headers, timeout=20)
        response.raise_for_status()
        return response.json()

    items = get("/search/issues", q=f"is:pr author:{login} -user:{login}", sort="created", order="desc",
                per_page=100)["items"]
    skipped = {name.lower() for name in exclude}
    projects = {}
    for full in {item["repository_url"].split("/repos/", 1)[1] for item in items}:
        if full.lower() in skipped:
            continue
        repo = get(f"/repos/{full}")
        # A token that can read private repositories would also find those; leave them out.
        if not repo["private"]:
            projects[full] = repo["stargazers_count"]

    pulls = []
    for item in items:
        full = item["repository_url"].split("/repos/", 1)[1]
        if projects.get(full, -1) < min_stars:
            continue
        merged = (item.get("pull_request") or {}).get("merged_at")
        pulls.append(PullRequest(full, item["title"].strip(), item["number"],
                                 "merged" if merged else item["state"], projects[full]))
    return pulls[:limit]
