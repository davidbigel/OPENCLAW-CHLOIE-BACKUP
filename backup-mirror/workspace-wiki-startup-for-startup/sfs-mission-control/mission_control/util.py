from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TOKEN_RE = re.compile(r"[A-Za-z0-9_\-]+|[\u0590-\u05ff]{2,}")

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "what",
    "how",
    "why",
    "are",
    "is",
    "של",
    "על",
    "את",
    "עם",
    "מה",
    "איך",
    "למה",
    "זה",
    "זאת",
    "האם",
    "יש",
    "אין",
    "אני",
    "אנחנו",
    "הוא",
    "היא",
    "הם",
    "הן",
    "או",
    "גם",
    "כל",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def compact_id(prefix: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    return f"{prefix}_{stamp}"


def tokenize(text: str) -> list[str]:
    seen: set[str] = set()
    tokens: list[str] = []
    for raw in TOKEN_RE.findall(text.lower()):
        token = raw.strip("-_")
        if len(token) < 2 or token in STOPWORDS:
            continue
        if token not in seen:
            seen.add(token)
            tokens.append(token)
    return tokens


def score_text(text: str, tokens: list[str], phrase: str = "") -> int:
    lower = text.lower()
    score = 0
    if phrase and len(phrase) > 4 and phrase.lower() in lower:
        score += 20
    for token in tokens:
        score += lower.count(token)
    return score


def strip_markdown(text: str) -> str:
    text = re.sub(r"~~~.*?~~~", " ", text, flags=re.S)
    text = re.sub(r"---.*?---", " ", text, count=1, flags=re.S)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"[#>*_\-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def excerpt_around(text: str, tokens: list[str], max_chars: int = 420) -> str:
    clean = strip_markdown(text)
    lower = clean.lower()
    pos = -1
    for token in tokens:
        pos = lower.find(token)
        if pos >= 0:
            break
    if pos < 0:
        return clean[:max_chars]
    start = max(0, pos - max_chars // 3)
    end = min(len(clean), start + max_chars)
    snippet = clean[start:end].strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(clean):
        snippet += "..."
    return snippet


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def first_heading(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip() or fallback
    return fallback


def ms_to_timecode(offset_ms: int | float | None) -> str:
    seconds = int((offset_ms or 0) // 1000)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def youtube_timestamp(video_id: str, offset_ms: int | float | None) -> str:
    seconds = int((offset_ms or 0) // 1000)
    return f"https://www.youtube.com/watch?v={video_id}&t={seconds}s"


def json_dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True)


def safe_html(text: str) -> str:
    return html.escape(text, quote=True)

