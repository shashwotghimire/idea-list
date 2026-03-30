from __future__ import annotations

import os
from collections.abc import Sequence
from contextlib import contextmanager
from urllib.parse import urlparse

from psycopg import OperationalError
from psycopg_pool import PoolTimeout
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

ALLOWED_DIFFICULTIES = {"weekend", "1-3 months", "6 months"}
ALLOWED_SOURCES = {"reddit", "github"}

DEMO_IDEAS: list[dict] = []


def _db_url() -> str:
    url = os.getenv("NEON_DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("NEON_DATABASE_URL is not set")
    return url


def _connect_kwargs() -> dict[str, object]:
    os.environ.pop("PGOPTIONS", None)
    return {"connect_timeout": 4}


_POOL: ConnectionPool | None = None


def _pool() -> ConnectionPool:
    global _POOL
    if _POOL is None:
        _POOL = ConnectionPool(
            conninfo=_db_url(),
            min_size=1,
            max_size=6,
            kwargs=_connect_kwargs(),
            open=True,
            timeout=8,
        )
    return _POOL


def _is_valid_source_url(source: str, source_url: str) -> bool:
    parsed = urlparse(source_url)
    host = parsed.netloc.lower()
    if source == "reddit":
        return host.endswith("reddit.com")
    if source == "github":
        return host.endswith("github.com")
    return False


def _looks_like_summary_row(title: str, problem: str) -> bool:
    title_l = title.lower().strip()
    problem_l = problem.lower().strip()
    title_starts = (
        "am i ",
        "when do i ",
        "should i ",
        "i built ",
        "i made ",
        "looking for ",
        "show me ",
        "friday share",
        "help me ",
    )
    banned = (
        "reddit",
        "post",
        "thread",
        "github repo",
        "the author",
        "the user",
        "shared on",
        "posted on",
    )
    if title_l.endswith("?") or title_l.startswith(title_starts):
        return True
    return any(token in title_l or token in problem_l for token in banned)


def _is_fallback_signature(
    audience: str, monetization: str, tags: list[str] | None
) -> bool:
    audience_l = audience.lower().strip()
    monetization_l = monetization.lower().strip()
    tags_l = [str(tag).lower().strip() for tag in (tags or [])]
    return (
        audience_l
        == "indie developers, small business operators, and service professionals"
        and monetization_l
        in {
            "subscription with optional premium templates and automation add-ons.",
            "subscription for advanced features.",
        }
        and tags_l == ["automation", "business", "workflow"]
    )


@contextmanager
def _cursor():
    with _pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            yield cur


def fetch_ideas(
    search: str | None,
    tag: str | None,
    difficulty: str | None,
    source: str | None,
    limit: int,
    offset: int,
) -> tuple[list[dict], int]:
    if os.getenv("USE_DEMO_DATA", "false").lower() == "true":
        items = [*DEMO_IDEAS]
        if search:
            q = search.lower().strip()
            items = [
                item
                for item in items
                if q in item["title"].lower()
                or q in (item.get("problem") or "").lower()
            ]
        if tag:
            t = tag.lower().strip()
            items = [
                item for item in items if t in [x.lower() for x in item.get("tags", [])]
            ]
        if difficulty and difficulty in ALLOWED_DIFFICULTIES:
            items = [item for item in items if item.get("difficulty") == difficulty]
        if source and source in ALLOWED_SOURCES:
            items = [item for item in items if item.get("source") == source]
        total = len(items)
        return items[offset : offset + limit], total

    clauses: list[str] = []
    params: list[object] = []

    if search:
        clauses.append("(title ILIKE %s OR problem ILIKE %s)")
        like = f"%{search.strip()}%"
        params.extend([like, like])

    if tag:
        clauses.append("%s = ANY(tags)")
        params.append(tag.strip().lower())

    if difficulty:
        if difficulty not in ALLOWED_DIFFICULTIES:
            raise ValueError("invalid difficulty")
        clauses.append("difficulty = %s")
        params.append(difficulty)

    if source:
        if source not in ALLOWED_SOURCES:
            raise ValueError("invalid source")
        clauses.append("source = %s")
        params.append(source)

    clauses.append(
        "((source = 'reddit' AND source_url ILIKE 'https://%%reddit.com/%%') OR (source = 'github' AND source_url ILIKE 'https://github.com/%%'))"
    )
    where_sql = f"WHERE {' AND '.join(clauses)}"
    list_sql = (
        "SELECT id, title, problem, audience, monetization, difficulty, source_url, source, tags, created_at, COUNT(*) OVER() AS total_count "
        f"FROM ideas {where_sql} "
        "ORDER BY created_at DESC, id DESC LIMIT %s OFFSET %s"
    )
    try:
        with _cursor() as cur:
            cur.execute(list_sql, [*params, limit, offset])
            rows = cur.fetchall()
        if not rows:
            return [], 0
        total = int(rows[0]["total_count"])
        cleaned_rows = []
        for row in rows:
            row_dict = dict(row)
            row_dict.pop("total_count", None)
            if (
                _is_valid_source_url(
                    str(row_dict.get("source", "")), str(row_dict.get("source_url", ""))
                )
                and not _looks_like_summary_row(
                    str(row_dict.get("title", "")), str(row_dict.get("problem", ""))
                )
                and not _is_fallback_signature(
                    str(row_dict.get("audience", "")),
                    str(row_dict.get("monetization", "")),
                    row_dict.get("tags"),
                )
            ):
                cleaned_rows.append(row_dict)
        return cleaned_rows, total
    except (OperationalError, PoolTimeout):
        return [], 0


def fetch_idea_by_id(idea_id: int) -> dict | None:
    if os.getenv("USE_DEMO_DATA", "false").lower() == "true":
        for item in DEMO_IDEAS:
            if int(item["id"]) == idea_id:
                return item
        return None

    sql = (
        "SELECT id, title, problem, audience, monetization, difficulty, source_url, source, tags, created_at "
        "FROM ideas WHERE id = %s"
    )
    try:
        with _cursor() as cur:
            cur.execute(sql, (idea_id,))
            row = cur.fetchone()
            if row is None:
                return None
            if not _is_valid_source_url(
                str(row.get("source", "")), str(row.get("source_url", ""))
            ):
                return None
            if _looks_like_summary_row(
                str(row.get("title", "")), str(row.get("problem", ""))
            ):
                return None
            if _is_fallback_signature(
                str(row.get("audience", "")),
                str(row.get("monetization", "")),
                row.get("tags"),
            ):
                return None
            return row
    except (OperationalError, PoolTimeout):
        return None


def fetch_tags() -> Sequence[str]:
    if os.getenv("USE_DEMO_DATA", "false").lower() == "true":
        tags: set[str] = set()
        for item in DEMO_IDEAS:
            tags.update(item.get("tags", []))
        return sorted(tags)

    sql = "SELECT DISTINCT unnest(tags) AS tag FROM ideas ORDER BY tag ASC"
    try:
        with _cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
        return [str(row["tag"]) for row in rows if row.get("tag")]
    except (OperationalError, PoolTimeout):
        return []
