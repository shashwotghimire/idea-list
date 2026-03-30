from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query

from api.db import DEMO_IDEAS, fetch_idea_by_id, fetch_ideas, fetch_tags
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
        if difficulty:
            items = [item for item in items if item.get("difficulty") == difficulty]
        if source:
            items = [item for item in items if item.get("source") == source]
        total = len(items)
        page = items[offset : offset + limit]
        return IdeasResponse(
            items=[Idea(**row) for row in page], total=total, limit=limit, offset=offset
        )

    try:
        rows, total = fetch_ideas(search, tag, difficulty, source, limit, offset)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return IdeasResponse(
        items=[Idea(**row) for row in rows], total=total, limit=limit, offset=offset
    )


@app.get("/ideas/{idea_id}", response_model=Idea)
def get_idea(idea_id: int) -> Idea:
    if os.getenv("USE_DEMO_DATA", "false").lower() == "true":
        for item in DEMO_IDEAS:
            if int(item["id"]) == idea_id:
                return Idea(**item)
        raise HTTPException(status_code=404, detail="idea not found")

    row = fetch_idea_by_id(idea_id)
    if row is None:
        raise HTTPException(status_code=404, detail="idea not found")
    return Idea(**row)


@app.get("/tags", response_model=list[str])
def get_tags() -> list[str]:
    if os.getenv("USE_DEMO_DATA", "false").lower() == "true":
        tags: set[str] = set()
        for item in DEMO_IDEAS:
            tags.update(item.get("tags", []))
        return sorted(tags)

    return list(fetch_tags())
