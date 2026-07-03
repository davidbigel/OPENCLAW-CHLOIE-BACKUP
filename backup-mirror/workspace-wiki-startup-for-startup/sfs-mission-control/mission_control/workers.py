from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import Config
from .util import (
    excerpt_around,
    first_heading,
    ms_to_timecode,
    read_text,
    score_text,
    tokenize,
    youtube_timestamp,
)


@dataclass
class WorkerResult:
    source: str
    status: str
    answer_markdown: str
    evidence: list[dict[str, Any]] = field(default_factory=list)
    citations: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def run_wikillm_worker(config: Config, question: str) -> WorkerResult:
    tokens = tokenize(question)
    if not config.wikillm_dir.exists():
        return WorkerResult(
            source="wikillm",
            status="failed",
            answer_markdown="No KB evidence: ספריית WikiLLM לא נמצאה.",
            errors=[f"missing path: {config.wikillm_dir}"],
        )
    matches: list[tuple[int, Path, str, str, str]] = []
    for path in config.wikillm_dir.rglob("*.md"):
        text = read_text(path)
        score = score_text(text, tokens, question)
        if score <= 0:
            continue
        title = first_heading(text, path.stem)
        matches.append((score, path, title, excerpt_around(text, tokens), text))
    matches.sort(key=lambda item: item[0], reverse=True)
    top = matches[:12]
    evidence: list[dict[str, Any]] = []
    for rank, (score, path, title, excerpt, text) in enumerate(top, start=1):
        item = {
            "source_type": "wikillm",
            "title": title,
            "path": str(path.relative_to(config.workspace_root)),
            "excerpt": excerpt,
            "rank": rank,
            "score": score,
        }
        item.update(_extract_wiki_citation(text))
        evidence.append(item)
    if not evidence:
        return WorkerResult(
            source="wikillm",
            status="no_useful_evidence",
            answer_markdown="No KB evidence: לא נמצאו דפי WikiLLM שמתאימים לשאלה.",
        )
    lines = [
        f"Corpus: מצאתי {len(matches)} דפי WikiLLM רלוונטיים, ומתוכם {len(evidence)} חזקים מספיק להצגה.",
        "",
    ]
    for item in evidence[:6]:
        lines.append(f"- {item['title']} ({item['path']}): {item['excerpt']}")
    return WorkerResult(
        source="wikillm",
        status="used",
        answer_markdown="\n".join(lines),
        evidence=evidence,
        citations=evidence,
    )


def run_obsidian_worker(config: Config, question: str) -> WorkerResult:
    return WorkerResult(
        source="obsidian",
        status="unavailable",
        answer_markdown="",
        evidence=[],
        citations=[],
    )


def run_raw_worker(config: Config, question: str) -> WorkerResult:
    tokens = tokenize(question)
    titles = load_video_titles(config.source_lists_dir)
    if not config.raw_dir.exists():
        return WorkerResult(
            source="raw",
            status="failed",
            answer_markdown="No KB evidence: ספריית התמלולים הגולמיים לא נמצאה.",
            errors=[f"missing path: {config.raw_dir}"],
        )
    evidence: list[dict[str, Any]] = []
    for path in sorted(config.raw_dir.glob("*.md")):
        video_id = path.stem
        segments = load_raw_segments(path)
        for idx, segment in enumerate(segments):
            text = str(segment.get("text") or "")
            if not _segment_matches(text, tokens, question):
                continue
            context = _segment_context(segments, idx)
            offset = segment.get("offset") or 0
            evidence.append(
                {
                    "source_type": "raw",
                    "title": titles.get(video_id, f"Raw Transcript - {video_id}"),
                    "video_id": video_id,
                    "timecode": ms_to_timecode(offset),
                    "url": youtube_timestamp(video_id, offset),
                    "path": str(path.relative_to(config.workspace_root)),
                    "quote": text,
                    "excerpt": context,
                    "rank": len(evidence) + 1,
                }
            )
    evidence.extend(_search_source_lists(config, tokens, question, start_rank=len(evidence) + 1))
    if not evidence:
        return WorkerResult(
            source="raw",
            status="no_useful_evidence",
            answer_markdown="No KB evidence: לא נמצאו התאמות בתמלולים הגולמיים.",
        )
    lines = [
        f"Raw: נמצאו {len(evidence)} התאמות בתמלולים. הציטוטים המלאים נמצאים בתיבה הגולמית ופתוחים בהרחבה לפי צורך.",
        "",
    ]
    for item in evidence[:8]:
        if item.get("video_id"):
            lines.append(f"- [{item['title']} | {item['video_id']} | {item['timecode']}] {item.get('quote') or item.get('excerpt', '')}")
        else:
            lines.append(f"- [{item['title']} | {item['source_type']}] {item.get('excerpt', '')}")
    if len(evidence) > 8:
        lines.append(f"- ועוד {len(evidence) - 8} התאמות שמורות בתיבת Raw Sources.")
    return WorkerResult(
        source="raw",
        status="used",
        answer_markdown="\n".join(lines),
        evidence=evidence,
        citations=evidence,
    )


def load_video_titles(source_lists_dir: Path) -> dict[str, str]:
    titles: dict[str, str] = {}
    if not source_lists_dir.exists():
        return titles
    current_title: str | None = None
    for path in sorted(source_lists_dir.glob("*.md")):
        for line in read_text(path).splitlines():
            heading = re.match(r"^###\s+\d+\.\s+(.+)$", line)
            if heading:
                current_title = heading.group(1).strip()
                continue
            video = re.match(r"^- Video ID:\s+(.+)$", line)
            if video and current_title:
                titles[video.group(1).strip()] = current_title
                current_title = None
    return titles


def _extract_wiki_citation(text: str) -> dict[str, str]:
    quote = ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("> ") and not stripped.startswith("> Source:"):
            quote = stripped.removeprefix("> ").strip().strip('"')
            continue
        if not stripped.startswith("> Source:"):
            continue
        parts = [part.strip() for part in stripped.removeprefix("> Source:").split("|")]
        if len(parts) < 5:
            continue
        episode_link = parts[0]
        title = " | ".join(parts[1:-3])
        video_id, timecode, url = parts[-3:]
        return {
            "title": title,
            "video_id": video_id,
            "timecode": timecode,
            "url": url,
            "quote": quote,
            "episode": episode_link,
        }
    return {}


def _search_source_lists(config: Config, tokens: list[str], question: str, start_rank: int) -> list[dict[str, Any]]:
    if not config.source_lists_dir.exists():
        return []
    items: list[dict[str, Any]] = []
    for path in sorted(config.source_lists_dir.glob("*.md")):
        text = read_text(path)
        if score_text(text, tokens, question) <= 0:
            continue
        items.append(
            {
                "source_type": "raw_metadata",
                "title": first_heading(text, path.stem),
                "path": str(path.relative_to(config.workspace_root)),
                "excerpt": excerpt_around(text, tokens),
                "rank": start_rank + len(items),
            }
        )
    return items


def load_raw_segments(path: Path) -> list[dict[str, Any]]:
    text = read_text(path)
    marker = "## Raw Supadata Result"
    if marker not in text:
        return []
    tail = text.split(marker, 1)[1]
    start = tail.find("{")
    end = tail.rfind("}")
    if start < 0 or end < start:
        return []
    try:
        payload = json.loads(tail[start : end + 1])
    except json.JSONDecodeError:
        return []
    content = payload.get("content")
    if isinstance(content, list):
        return [item for item in content if isinstance(item, dict)]
    return []


def _segment_matches(text: str, tokens: list[str], phrase: str) -> bool:
    lower = text.lower()
    if phrase and len(phrase) > 4 and phrase.lower() in lower:
        return True
    return any(token in lower for token in tokens)


def _segment_context(segments: list[dict[str, Any]], index: int) -> str:
    start = max(0, index - 1)
    end = min(len(segments), index + 2)
    return " ".join(str(segments[i].get("text") or "") for i in range(start, end)).strip()
