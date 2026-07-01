from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Iterable, Mapping, Sequence

STOPWORDS = {
    "a",
    "about",
    "after",
    "all",
    "also",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "because",
    "been",
    "but",
    "by",
    "can",
    "could",
    "did",
    "do",
    "does",
    "for",
    "from",
    "had",
    "has",
    "have",
    "he",
    "her",
    "him",
    "his",
    "how",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "just",
    "may",
    "me",
    "more",
    "most",
    "my",
    "no",
    "not",
    "of",
    "on",
    "or",
    "our",
    "out",
    "over",
    "said",
    "she",
    "so",
    "some",
    "than",
    "that",
    "the",
    "their",
    "them",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "to",
    "too",
    "up",
    "us",
    "was",
    "we",
    "were",
    "what",
    "when",
    "which",
    "who",
    "will",
    "with",
    "would",
    "you",
    "your",
}

SPEAKER_RE = re.compile(
    r"^(?:(?P<timestamp>\d{1,2}:\d{2}(?::\d{2})?)\s+)?(?P<speaker>[A-Z][A-Za-z0-9][A-Za-z0-9 .,'&()/\-]{0,60}):\s+(?P<text>.+)$"
)
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9']+")
CAPITALIZED_RE = re.compile(r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b")
QUOTE_RE = re.compile(r"[\"“](.+?)[\"”]")


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-") or "item"


def stable_hash(*parts: str, length: int = 12) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()[:length]


def checksum_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def checksum_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u200b", "")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("#"):
            lines.append(line.rstrip())
        elif SPEAKER_RE.match(line):
            lines.append(line)
        else:
            lines.append(re.sub(r"\s{2,}", " ", line))
    return "\n".join(lines).strip()


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    block = match.group(1)
    body = text[match.end() :]
    metadata: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata, body


def render_frontmatter(metadata: Mapping[str, object]) -> str:
    lines = ["---"]
    for key, value in metadata.items():
        lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    lines.append("---")
    return "\n".join(lines)


def extract_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = HEADING_RE.match(stripped)
        if match:
            return match.group(2).strip()
        if stripped.lower().startswith(("title:", "episode:", "name:")) and ":" in stripped:
            return stripped.split(":", 1)[1].strip()
        return stripped[:120]
    return fallback


def sentence_split(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [part.strip() for part in parts if part.strip()]


def chunk_words(text: str) -> list[str]:
    return [word.lower() for word in TOKEN_RE.findall(text)]


def top_keywords(texts: Iterable[str], limit: int = 10) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    for text in texts:
        for token in chunk_words(text):
            if len(token) < 3 or token in STOPWORDS:
                continue
            counter[token] += 1
    return counter.most_common(limit)


def extract_capitalized_phrases(text: str, limit: int = 20) -> list[str]:
    phrases = []
    for match in CAPITALIZED_RE.findall(text):
        cleaned = match.strip()
        if cleaned.lower() not in STOPWORDS:
            phrases.append(cleaned)
    unique: list[str] = []
    seen: set[str] = set()
    for phrase in phrases:
        key = phrase.lower()
        if key not in seen:
            seen.add(key)
            unique.append(phrase)
        if len(unique) >= limit:
            break
    return unique


def extract_quotes(text: str, limit: int = 10) -> list[str]:
    quotes = [match.strip() for match in QUOTE_RE.findall(text) if len(match.strip()) > 12]
    unique: list[str] = []
    seen: set[str] = set()
    for quote in quotes:
        key = quote.lower()
        if key not in seen:
            seen.add(key)
            unique.append(quote)
        if len(unique) >= limit:
            break
    return unique


def rel_path(base: Path, target: Path) -> str:
    return target.relative_to(base).as_posix()


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def json_dump(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def json_load(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def md_link(title: str, target: str) -> str:
    return f"[[{title}|{target}]]" if title != target else f"[[{title}]]"


def unique_sorted(values: Sequence[str]) -> list[str]:
    return sorted({value for value in values if value})
