from __future__ import annotations

import json
import os
from dataclasses import dataclass

import requests

SYSTEM_PROMPT = """You are an expert at identifying side project and startup ideas from online discussions.

You will be given a Reddit post (title + body). Your job is to extract or infer a concrete, buildable side project idea from it.

Rules:
- The idea must be a specific product someone could build - not a summary of the post
- If the post complains about a problem, turn that problem into a product idea
- If the post describes something the author built or wishes existed, extract that as the idea
- If no clear buildable idea can be extracted, return { "skip": true }
- Never use the Reddit post title as the idea title
- Never summarize the post - always think "what could someone BUILD because of this?"

Respond ONLY with valid JSON, no explanation, no markdown:

{
  "title": "Name of the product idea (max 6 words, not the post title)",
  "problem": "The specific problem this product solves (1-2 sentences)",
  "audience": "Specific target user - not 'everyone' or 'developers'",
  "monetization": "One realistic way this makes money",
  "difficulty": "one of: weekend, 1-3 months, 6 months",
  "tags": ["2-4 relevant tags"]
}"""

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


def _is_summary_like_text(text: str) -> bool:
    lowered = text.lower()
    banned_phrases = [
        "i built",
        "my project",
        "this post",
        "the post",
        "this repo",
        "the repo",
        "on reddit",
        "on github",
        "reddit post",
        "github repo",
    ]
    return any(phrase in lowered for phrase in banned_phrases)


def _validate(data: dict, source_title: str) -> IdeaCandidate | None:
    if data.get("skip") is True:
        return None
    difficulty = str(data.get("difficulty") or "").strip()
    if difficulty not in ALLOWED_DIFFICULTIES:
        return None
    tags = [
        str(tag).strip().lower() for tag in data.get("tags", []) if str(tag).strip()
    ]
    if not (2 <= len(tags) <= 4):
        return None
    fields = ["title", "problem", "audience", "monetization"]
    if any(not str(data.get(field) or "").strip() for field in fields):
        return None
    title = str(data["title"]).strip()
    if not 2 <= len(title.split()) <= 6:
        return None
    if _is_too_similar_title(title, source_title):
        return None
    problem = str(data["problem"]).strip()
    if _is_summary_like_text(problem):
        return None
    if len(problem) < 30 or len(problem) > 240:
        return None
    return IdeaCandidate(
        title=title,
        problem=problem,
        audience=str(data["audience"]).strip(),
        monetization=str(data["monetization"]).strip(),
        difficulty=difficulty,
        tags=tags,
    )


def extract_with_kimi(source_title: str, content: str) -> IdeaCandidate | None:
    api_key = os.getenv("KIMI_API_KEY", "").strip()
    if not api_key:
        return None
    user_prompt = f"Reddit post content:\n\n{content[:6000]}"
    payload = {
        "model": "moonshot-v1-8k",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.45,
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
