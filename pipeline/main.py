from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

try:
    from .db import IdeaRecord, ensure_schema, exists_source_url, insert_idea
    from .processor import extract_with_kimi
    from .scraper import scrape_all
except ImportError:
    from db import IdeaRecord, ensure_schema, exists_source_url, insert_idea
    from processor import extract_with_kimi
    from scraper import scrape_all


def main() -> None:
    load_dotenv(Path(__file__).with_name(".env"))
    ensure_schema()
    raw_items = scrape_all()
    inserted = 0
    skipped = 0
    for raw in raw_items:
        if exists_source_url(raw.source_url):
            skipped += 1
            continue
        candidate = extract_with_kimi(raw.content)
        if candidate is None:
            skipped += 1
            continue
        record = IdeaRecord(
            title=candidate.title,
            problem=candidate.problem,
            audience=candidate.audience,
            monetization=candidate.monetization,
            difficulty=candidate.difficulty,
            source_url=raw.source_url,
            source=raw.source,
            tags=candidate.tags,
        )
        created = insert_idea(record)
        if created is None:
            skipped += 1
            continue
        inserted += 1
    print(f"Pipeline complete. inserted={inserted} skipped={skipped}")


if __name__ == "__main__":
    main()
