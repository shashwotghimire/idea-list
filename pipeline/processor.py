from __future__ import annotations

import json
import os
from dataclasses import dataclass

import requests

PROMPT_TEMPLATE = """You are extracting side project ideas from Reddit posts and GitHub repos.

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
__CONTENT__
"""

ALLOWED_DIFFICULTIES = {"weekend", "1-3 months", "6 months"}


@dataclass
class IdeaCandidate:
    title: str
    problem: str
    audience: str
    monetization: str
    difficulty: str
    tags: list[str]


def _fallback_extract(content: str) -> IdeaCandidate | None:
    cleaned = " ".join(content.split())
    if len(cleaned) < 40:
        return None
    title = cleaned[:56].strip().split(" ")[:8]
    return IdeaCandidate(
        title=" ".join(title),
        problem=cleaned[:180],
        audience="Makers and indie developers",
        monetization="Subscription for advanced features.",
        difficulty="1-3 months",
        tags=["saas", "automation"],
    )


def _validate(data: dict) -> IdeaCandidate | None:
    if data.get("skip") is True:
        return None
    difficulty = str(data.get("difficulty") or "").strip()
    if difficulty not in ALLOWED_DIFFICULTIES:
        return None
    tags = [
        str(tag).strip().lower() for tag in data.get("tags", []) if str(tag).strip()
    ]
    if not tags:
        return None
    fields = ["title", "problem", "audience", "monetization"]
    if any(not str(data.get(field) or "").strip() for field in fields):
        return None
    return IdeaCandidate(
        title=str(data["title"]).strip(),
        problem=str(data["problem"]).strip(),
        audience=str(data["audience"]).strip(),
        monetization=str(data["monetization"]).strip(),
        difficulty=difficulty,
        tags=tags,
    )


def extract_with_kimi(content: str) -> IdeaCandidate | None:
    api_key = os.getenv("KIMI_API_KEY", "").strip()
    if not api_key:
        return _fallback_extract(content)
    prompt = PROMPT_TEMPLATE.replace("__CONTENT__", content[:6000])
    payload = {
        "model": "moonshot-v1-8k",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }
    try:
        response = requests.post(
            "https://api.moonshot.ai/v1/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30,
        )
        response.raise_for_status()
        body = response.json()
        message = body["choices"][0]["message"]["content"]
        data = json.loads(message)
        return _validate(data)
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError):
        return _fallback_extract(content)
