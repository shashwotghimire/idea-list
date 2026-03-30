from __future__ import annotations

import json
import os
from dataclasses import dataclass

import requests

PROMPT_TEMPLATE = """You are extracting side project ideas from Reddit posts and GitHub repos.
You must rewrite and improve the idea.
Do not copy the original post/repo title directly; generate a new project title.
Create tags that can include both technical and non-technical audience signals.
Audience should be explicit and may include non-technical people such as operators, teachers, coaches, recruiters, creators, or small business owners.

Given the following content, extract a side project idea if one exists.
If no clear idea exists, return null.

Respond ONLY with a valid JSON object in this exact format, nothing else:
{
  "title": "new project title (3-8 words, not the original post/repo title)",
  "problem": "short project description (1 sentence, concise)",
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


def _normalize_text(value: str) -> str:
    allowed = [ch.lower() if ch.isalnum() or ch.isspace() else " " for ch in value]
    return " ".join("".join(allowed).split())


def _is_too_similar_title(generated_title: str, source_title: str) -> bool:
    g_norm = _normalize_text(generated_title)
    s_norm = _normalize_text(source_title)
    if not g_norm or not s_norm:
        return False
    if g_norm == s_norm:
        return True
    g_tokens = g_norm.split()
    s_tokens = s_norm.split()
    return g_tokens[:4] == s_tokens[:4]


def _fallback_extract(content: str) -> IdeaCandidate | None:
    cleaned = " ".join(content.split())
    if len(cleaned) < 40:
        return None
    title = cleaned[:56].strip().split(" ")[:8]
    return IdeaCandidate(
        title=" ".join(title).replace("/", " "),
        problem=cleaned[:180],
        audience="Indie developers, small business operators, and service professionals",
        monetization="Subscription with optional premium templates and automation add-ons.",
        difficulty="1-3 months",
        tags=["automation", "business", "workflow"],
    )


def _validate(data: dict, source_title: str) -> IdeaCandidate | None:
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
    title = str(data["title"]).strip()
    if _is_too_similar_title(title, source_title):
        return None
    return IdeaCandidate(
        title=title,
        problem=str(data["problem"]).strip(),
        audience=str(data["audience"]).strip(),
        monetization=str(data["monetization"]).strip(),
        difficulty=difficulty,
        tags=tags,
    )


def extract_with_kimi(source_title: str, content: str) -> IdeaCandidate | None:
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
        return _validate(data, source_title)
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError):
        return None
