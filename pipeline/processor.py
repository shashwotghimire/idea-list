from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import requests

SYSTEM_PROMPT = """You are an expert startup ideation model.

Task:
Convert a Reddit/GitHub source text into ONE new, buildable product idea.

Hard constraints:
1) DO NOT summarize, paraphrase, or describe what the author posted.
2) DO NOT mention "post", "reddit", "github", "repo", "author", "user", "thread", or "shared".
3) DO NOT use first-person phrasing such as "I built", "I made", "my app".
4) Title must be newly generated and MUST NOT reuse source title wording.
5) If you cannot infer a concrete product idea, output exactly: { "skip": true }

Output intent:
- Treat the source as signal only.
- Synthesize a product someone can build next.
- Write from product perspective, not source perspective.

Quality bar:
- Title: 2-6 words, product-style name.
- Problem: 1-2 sentences describing the product's solved pain and core approach.
- Audience: a specific user segment (never generic terms like everyone/developers).
- Monetization: one realistic model.
- Difficulty: weekend | 1-3 months | 6 months.
- Tags: 2-4 practical tags.

Return ONLY valid JSON, no markdown, no extra text:
{
  "title": "Name of the product idea (max 6 words, not source title)",
  "problem": "Specific pain solved and the product approach (1-2 sentences)",
  "audience": "Specific target user segment",
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
        "i made",
        "i created",
        "show me your",
        "let's share",
        "this is a post",
        "post about",
        "shared this",
        "looking for advice",
        "feedback on",
        "my project",
        "this post",
        "the post",
        "this repo",
        "the repo",
        "on reddit",
        "on github",
        "reddit post",
        "github repo",
        "the author",
        "the user",
        "shared on",
        "posted on",
        "thread",
        "the author posted",
        "the user posted",
    ]
    return any(phrase in lowered for phrase in banned_phrases)


def _is_invalid_audience(audience: str) -> bool:
    lowered = audience.lower().strip()
    banned = {"everyone", "developers", "all users", "anyone"}
    return lowered in banned


def _parse_response(content: str) -> dict[str, Any] | None:
    raw = content.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            return json.loads(raw[start : end + 1])
        except json.JSONDecodeError:
            return None


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
    if _is_summary_like_text(title):
        return None
    problem = str(data["problem"]).strip()
    if _is_summary_like_text(problem):
        return None
    if len(problem) < 30 or len(problem) > 240:
        return None
    audience = str(data["audience"]).strip()
    if _is_invalid_audience(audience):
        return None
    return IdeaCandidate(
        title=title,
        problem=problem,
        audience=audience,
        monetization=str(data["monetization"]).strip(),
        difficulty=difficulty,
        tags=tags,
    )


def extract_with_kimi(source_title: str, content: str) -> IdeaCandidate | None:
    api_key = os.getenv("KIMI_API_KEY", "").strip()
    if not api_key:
        return None
    user_prompt = f"Reddit post content:\n\n{content[:6000]}"
    messages: list[dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    try:
        for attempt in range(2):
            payload = {
                "model": "moonshot-v1-8k",
                "messages": messages,
                "temperature": 0.45,
            }
            response = requests.post(
                "https://api.moonshot.ai/v1/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=30,
            )
            response.raise_for_status()
            body = response.json()
            message = body["choices"][0]["message"]["content"]
            data = _parse_response(message)
            if data is not None:
                candidate = _validate(data, source_title)
                if candidate is not None:
                    return candidate
            if attempt == 0:
                messages.append({"role": "assistant", "content": message})
                messages.append(
                    {
                        "role": "user",
                        "content": "Your previous answer summarized the source or violated format constraints. Rewrite it as a concrete product idea and return only valid JSON.",
                    }
                )
        return None
    except (requests.RequestException, KeyError, IndexError, TypeError):
        return None
