from __future__ import annotations

import os
from collections.abc import Sequence

from psycopg import connect
from psycopg.rows import dict_row

ALLOWED_DIFFICULTIES = {"weekend", "1-3 months", "6 months"}
ALLOWED_SOURCES = {"reddit", "github"}


def _db_url() -> str:
    url = os.getenv("NEON_DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("NEON_DATABASE_URL is not set")
    return url


def fetch_ideas(
    search: str | None,
    tag: str | None,
    difficulty: str | None,
    source: str | None,
    limit: int,
    offset: int,
) -> tuple[list[dict], int]:
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
    count_sql = f"SELECT COUNT(*) AS total FROM ideas {where_sql}"
    list_sql = (
        "SELECT id, title, problem, audience, monetization, difficulty, source_url, source, tags, created_at "
        f"FROM ideas {where_sql} "
        "ORDER BY created_at DESC, id DESC LIMIT %s OFFSET %s"
    )
    with connect(_db_url()) as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(count_sql, params)
        total = int(cur.fetchone()["total"])
        cur.execute(list_sql, [*params, limit, offset])
        rows = cur.fetchall()
    return list(rows), total


def fetch_idea_by_id(idea_id: int) -> dict | None:
    sql = (
        "SELECT id, title, problem, audience, monetization, difficulty, source_url, source, tags, created_at "
        "FROM ideas WHERE id = %s"
    )
    with connect(_db_url()) as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, (idea_id,))
        return cur.fetchone()


def fetch_tags() -> Sequence[str]:
    sql = "SELECT DISTINCT unnest(tags) AS tag FROM ideas ORDER BY tag ASC"
    with connect(_db_url()) as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql)
        rows = cur.fetchall()
    return [str(row["tag"]) for row in rows if row.get("tag")]
