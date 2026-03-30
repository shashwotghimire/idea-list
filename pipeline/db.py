from __future__ import annotations

import os
from dataclasses import asdict, dataclass

from psycopg import connect
from psycopg.rows import dict_row


@dataclass
class IdeaRecord:
    title: str
    problem: str
    audience: str
    monetization: str
    difficulty: str
    source_url: str
    source: str
    tags: list[str]


def _db_url() -> str:
    url = os.getenv("NEON_DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("NEON_DATABASE_URL is not set")
    return url


def ensure_schema() -> None:
    ddl = """
    CREATE TABLE IF NOT EXISTS ideas (
      id SERIAL PRIMARY KEY,
      title TEXT NOT NULL,
      problem TEXT,
      audience TEXT,
      monetization TEXT,
      difficulty TEXT CHECK (difficulty IN ('weekend', '1-3 months', '6 months')),
      source_url TEXT UNIQUE,
      source TEXT CHECK (source IN ('reddit', 'github')),
      tags TEXT[],
      created_at TIMESTAMP DEFAULT NOW()
    );
    """
    with connect(_db_url()) as conn, conn.cursor() as cur:
        cur.execute(ddl)
        conn.commit()


def exists_source_url(source_url: str) -> bool:
    sql = "SELECT 1 FROM ideas WHERE source_url = %s LIMIT 1"
    with connect(_db_url()) as conn, conn.cursor() as cur:
        cur.execute(sql, (source_url,))
        return cur.fetchone() is not None


def insert_idea(idea: IdeaRecord) -> int | None:
    sql = """
    INSERT INTO ideas (title, problem, audience, monetization, difficulty, source_url, source, tags)
    VALUES (%(title)s, %(problem)s, %(audience)s, %(monetization)s, %(difficulty)s, %(source_url)s, %(source)s, %(tags)s)
    ON CONFLICT (source_url) DO NOTHING
    RETURNING id
    """
    with connect(_db_url()) as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, asdict(idea))
        row = cur.fetchone()
        conn.commit()
        return None if row is None else int(row["id"])
