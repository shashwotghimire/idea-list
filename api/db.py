from __future__ import annotations

import os
from collections.abc import Sequence
from contextlib import contextmanager

from psycopg import connect
from psycopg.rows import dict_row

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
    return {"connect_timeout": 8}


@contextmanager
def _cursor():
    with connect(_db_url(), **_connect_kwargs()) as conn:
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

    where_sql = "" if not clauses else f"WHERE {' AND '.join(clauses)}"
    list_sql = (
        "SELECT id, title, problem, audience, monetization, difficulty, source_url, source, tags, created_at "
        f"FROM ideas {where_sql} "
        "ORDER BY created_at DESC, id DESC LIMIT %s OFFSET %s"
    )
    with _cursor() as cur:
        cur.execute(list_sql, [*params, limit, offset])
        rows = cur.fetchall()
    total = offset + len(rows)
    return list(rows), total


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
    with _cursor() as cur:
        cur.execute(sql, (idea_id,))
        return cur.fetchone()


def fetch_tags() -> Sequence[str]:
    if os.getenv("USE_DEMO_DATA", "false").lower() == "true":
        tags: set[str] = set()
        for item in DEMO_IDEAS:
            tags.update(item.get("tags", []))
        return sorted(tags)

    sql = "SELECT DISTINCT unnest(tags) AS tag FROM ideas ORDER BY tag ASC"
    with _cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()
    return [str(row["tag"]) for row in rows if row.get("tag")]
