from __future__ import annotations

from pipeline.scraper import RawItem


def test_extract_side_project() -> None:
    item = RawItem(
        title="AI tool",
        content="A useful AI coding helper for founders",
        source_url="https://example.com",
        source="reddit",
        score=42,
    )
    assert item.source == "reddit"
    assert item.source_url.startswith("https://")
