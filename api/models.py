from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Idea(BaseModel):
    id: int
    title: str
    problem: str | None = None
    audience: str | None = None
    monetization: str | None = None
    difficulty: str | None = None
    source_url: str
    source: str
    tags: list[str] = Field(default_factory=list)
    created_at: datetime | None = None


class IdeasResponse(BaseModel):
    items: list[Idea]
    total: int
    limit: int
    offset: int
