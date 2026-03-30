from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import requests

REDDIT_SUBREDDITS = [
    "SideProject",
    "entrepreneur",
    "buildinpublic",
    "startups",
    "webdev",
    "indiehackers",
    "smallbusiness",
    "freelance",
    "EntrepreneurRideAlong",
    "SaaS",
]

GITHUB_TOPICS = [
    "side-project",
    "indie",
    "saas",
    "productivity",
    "small-business",
    "education",
    "automation",
]
GITHUB_QUERIES = [
    "topic:side-project stars:>30",
    "topic:saas stars:>30",
    "topic:productivity stars:>25",
    "topic:small-business stars:>15",
    "micro-saas stars:>20",
    "internal tool stars:>20",
    "automation tool stars:>20",
]


@dataclass
class RawItem:
    title: str
    content: str
    source_url: str
    source: str
    score: int


def _safe_get(url: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    try:
        response = requests.get(
            url,
            params=params,
            timeout=15,
            headers={"User-Agent": "idea-list/1.0"},
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


def scrape_reddit(min_score: int = 15, per_subreddit: int = 20) -> list[RawItem]:
    items: list[RawItem] = []
    for subreddit in REDDIT_SUBREDDITS:
        data = _safe_get(
            f"https://www.reddit.com/r/{subreddit}/hot.json",
            params={"limit": per_subreddit},
        )
        if not data:
            continue
        posts = data.get("data", {}).get("children", [])
        for post in posts:
            p = post.get("data", {})
            score = int(p.get("score") or 0)
            if score < min_score:
                continue
            title = str(p.get("title") or "").strip()
            body = str(p.get("selftext") or "").strip()
            permalink = p.get("permalink") or ""
            source_url = f"https://www.reddit.com{permalink}" if permalink else ""
            if not title or not source_url:
                continue
            items.append(
                RawItem(
                    title=title,
                    content=f"{title}\n\n{body}".strip(),
                    source_url=source_url,
                    source="reddit",
                    score=score,
                )
            )
    return items


def scrape_github(max_repos: int = 20) -> list[RawItem]:
    date_filter = datetime.now(UTC).strftime("%Y-%m-%d")
    items: list[RawItem] = []
    for query in [
        *GITHUB_QUERIES,
        *[f"topic:{topic} stars:>20" for topic in GITHUB_TOPICS],
    ]:
        params = {
            "q": f"{query} pushed:>={date_filter}",
            "sort": "stars",
            "order": "desc",
            "per_page": str(max_repos),
        }
        data = _safe_get("https://api.github.com/search/repositories", params=params)
        if not data:
            continue
        for repo in data.get("items", []):
            name = str(repo.get("full_name") or repo.get("name") or "").strip()
            desc = str(repo.get("description") or "").strip()
            url = str(repo.get("html_url") or "").strip()
            stars = int(repo.get("stargazers_count") or 0)
            topics = repo.get("topics") or []
            if not name or not url:
                continue
            if not url.startswith("https://github.com/"):
                continue
            topic_line = ", ".join([str(topic) for topic in topics if topic])
            items.append(
                RawItem(
                    title=name,
                    content=f"{name}\n\n{desc}\n\nTopics: {topic_line}".strip(),
                    source_url=url,
                    source="github",
                    score=stars,
                )
            )
    return items


def scrape_all() -> list[RawItem]:
    scraped = [*scrape_reddit(), *scrape_github()]
    deduped: dict[str, RawItem] = {
        item.source_url: item for item in scraped if item.source_url
    }
    return list(deduped.values())
