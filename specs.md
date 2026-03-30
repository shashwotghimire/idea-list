# idea-list Specs

## Overview

`idea-list` is a public directory of curated side project ideas sourced from Reddit and GitHub. A Python pipeline scrapes data periodically, processes it with Kimi AI, and stores structured ideas in a PostgreSQL database. A React frontend displays the ideas with search and filter.

## Stack

| Layer | Technology |
| --- | --- |
| Scraper + Pipeline | Python |
| AI Processing | Kimi API (free tier) |
| Database | Neon PostgreSQL |
| Backend API | FastAPI |
| Frontend | React + Vite |

## Project Structure

```text
idea-list/
|-- pipeline/
|   |-- main.py           # Entry point - runs full pipeline
|   |-- scraper.py        # Reddit + GitHub scrapers
|   |-- processor.py      # Kimi API processing
|   |-- db.py             # Neon DB connection + insert logic
|   |-- requirements.txt
|   `-- .env
|-- api/
|   |-- main.py           # FastAPI app
|   |-- db.py             # DB connection + queries
|   |-- models.py         # Pydantic models
|   `-- requirements.txt
|-- frontend/
|   |-- src/
|   |   |-- App.jsx
|   |   |-- components/
|   |   |   |-- IdeaCard.jsx
|   |   |   |-- SearchBar.jsx
|   |   |   `-- Filters.jsx
|   |   `-- api.js        # Fetch calls to FastAPI
|   |-- index.html
|   |-- package.json
|   `-- vite.config.js
`-- README.md
```

## Database Schema

```sql
CREATE TABLE ideas (
  id            SERIAL PRIMARY KEY,
  title         TEXT NOT NULL,
  problem       TEXT,
  audience      TEXT,
  monetization  TEXT,
  difficulty    TEXT CHECK (difficulty IN ('weekend', '1-3 months', '6 months')),
  source_url    TEXT,
  source        TEXT CHECK (source IN ('reddit', 'github')),
  tags          TEXT[],
  created_at    TIMESTAMP DEFAULT NOW()
);
```

## Pipeline Flow

1. Scrape Reddit posts from target subreddits via PRAW.
2. Scrape GitHub trending repos via GitHub API or web scraping.
3. Filter out low-signal posts (below upvote threshold, etc.).
4. Send each post to Kimi with extraction prompt.
5. Parse structured JSON response from Kimi.
6. Deduplicate against existing DB entries (check `source_url`).
7. Insert new ideas into Neon PostgreSQL.
8. Run on schedule via GitHub Actions cron.

## Target Subreddits

- `r/SideProject`
- `r/entrepreneur`
- `r/buildinpublic`
- `r/startups`
- `r/webdev`
- `r/indiehackers`

## GitHub Signal

- GitHub Trending (daily)
- Repos with rapid star growth
- Topics: `side-project`, `indie`, `saas`, `tool`

## Kimi Extraction Prompt

```text
You are extracting side project ideas from Reddit posts and GitHub repos.

Given the following content, extract a side project idea if one exists.
If no clear idea exists, return null.

Respond ONLY with a valid JSON object in this exact format, nothing else:
{
  "title": "short punchy name for the idea (max 8 words)",
  "problem": "what problem this solves (1-2 sentences)",
  "audience": "who this is for (specific, not 'everyone')",
  "monetization": "how this could make money (1 sentence)",
  "difficulty": "one of: weekend, 1-3 months, 6 months",
  "tags": ["array", "of", "relevant", "tags"]
}

If no clear side project idea can be extracted, return:
{ "skip": true }

Content:
{content}
```

## FastAPI Endpoints

### `GET /ideas`

Query params:

- `search` (string): searches `title` + `problem`
- `tag` (string): filter by tag
- `difficulty` (string): filter by difficulty
- `source` (string): `reddit` or `github`
- `limit` (int): default 20
- `offset` (int): default 0 (pagination)

### `GET /ideas/{id}`

Returns a single idea by ID.

### `GET /tags`

Returns list of all unique tags in DB.

## Frontend Pages

- `/`: main page, idea cards grid, search bar, filters
- `/idea/:id`: single idea detail page (optional, V0)

`IdeaCard` displays:

- Title
- Problem (truncated)
- Audience
- Difficulty badge
- Tags
- Source (Reddit / GitHub) with link

Filters:

- Search (text input)
- Difficulty (`weekend`, `1-3 months`, `6 months`)
- Source (Reddit / GitHub)
- Tags (multi-select)

## Environment Variables

### `pipeline/.env`

```env
KIMI_API_KEY=
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=idea-list/1.0
NEON_DATABASE_URL=
```

### `api/.env`

```env
NEON_DATABASE_URL=
```

### `frontend/.env`

```env
VITE_API_URL=http://localhost:8000
```

## GitHub Actions Cron (Pipeline)

```yaml
name: Run idea-list Pipeline
on:
  schedule:
    - cron: '0 0 * * *'  # daily at midnight UTC
  workflow_dispatch:      # manual trigger

jobs:
  pipeline:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r pipeline/requirements.txt
      - run: python pipeline/main.py
        env:
          KIMI_API_KEY: ${{ secrets.KIMI_API_KEY }}
          REDDIT_CLIENT_ID: ${{ secrets.REDDIT_CLIENT_ID }}
          REDDIT_CLIENT_SECRET: ${{ secrets.REDDIT_CLIENT_SECRET }}
          REDDIT_USER_AGENT: idea-list/1.0
          NEON_DATABASE_URL: ${{ secrets.NEON_DATABASE_URL }}
```

## V0 Scope

### In

- Python pipeline (Reddit + GitHub scraping)
- Kimi processing + structured extraction
- Neon PostgreSQL storage with deduplication
- FastAPI with 3 endpoints
- React + Vite frontend with cards, search, filters
- GitHub Actions cron for daily pipeline runs

### Out (post-V0)

- User accounts / bookmarking
- Upvoting ideas
- Submit your own idea
- Email digest
- Advanced scoring / ranking
- Idea detail page
