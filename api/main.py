from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query

from api.db import fetch_idea_by_id, fetch_ideas, fetch_tags
from api.models import Idea, IdeasResponse

load_dotenv(Path(__file__).with_name(".env"))

app = FastAPI(title="idea-list API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ideas", response_model=IdeasResponse)
def get_ideas(
    search: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    difficulty: str | None = Query(default=None),
    source: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> IdeasResponse:
    try:
        rows, total = fetch_ideas(search, tag, difficulty, source, limit, offset)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return IdeasResponse(
        items=[Idea(**row) for row in rows], total=total, limit=limit, offset=offset
    )


@app.get("/ideas/{idea_id}", response_model=Idea)
def get_idea(idea_id: int) -> Idea:
    row = fetch_idea_by_id(idea_id)
    if row is None:
        raise HTTPException(status_code=404, detail="idea not found")
    return Idea(**row)


@app.get("/tags", response_model=list[str])
def get_tags() -> list[str]:
    return list(fetch_tags())
