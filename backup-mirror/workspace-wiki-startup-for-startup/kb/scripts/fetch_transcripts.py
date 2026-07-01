#!/usr/bin/env python3
"""Fetch YouTube transcripts from Supadata into markdown files.

The script accepts any text/markdown file containing YouTube URLs or plain
11-character YouTube video IDs. Existing output files are skipped by default so
the fetch can be resumed safely.

Example:
    python3 kb/scripts/fetch_transcripts.py "kb/sources/lists/2026 06 30.md" --limit 4
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
URL_RE = re.compile(r"https?://[^\s<>)\"']+")
EXPLICIT_ID_RE = re.compile(
    r"\b(?:video\s*id|video_id|youtube\s*id|youtube_id)\s*[:=]\s*([A-Za-z0-9_-]{11})\b",
    re.IGNORECASE,
)

SCRIPT_PATH = Path(__file__).resolve()
KB_ROOT = SCRIPT_PATH.parents[1]
DEFAULT_ENV_FILE = KB_ROOT / ".env"
DEFAULT_OUTPUT_DIR = KB_ROOT / "sources" / "raw"


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


def normalize_video_id(value: str) -> str | None:
    value = value.strip()
    if VIDEO_ID_RE.fullmatch(value):
        return value
    return None


def video_id_from_url(raw_url: str) -> str | None:
    url = raw_url.rstrip(".,;:]}")
    parsed = urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.")

    if host in {"youtu.be", "youtube.com", "m.youtube.com", "music.youtube.com"}:
        if host == "youtu.be":
            candidate = parsed.path.strip("/").split("/", 1)[0]
            return normalize_video_id(candidate)

        if parsed.path == "/watch":
            candidate = parse_qs(parsed.query).get("v", [""])[0]
            return normalize_video_id(candidate)

        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) >= 2 and parts[0] in {"embed", "shorts", "live"}:
            return normalize_video_id(parts[1])

    return None


def extract_video_ids(input_path: Path) -> list[str]:
    seen: set[str] = set()
    video_ids: list[str] = []

    def add(video_id: str | None) -> None:
        if video_id and video_id not in seen:
            seen.add(video_id)
            video_ids.append(video_id)

    for line in input_path.read_text(encoding="utf-8").splitlines():
        for url in URL_RE.findall(line):
            add(video_id_from_url(url))

        explicit = EXPLICIT_ID_RE.search(line)
        if explicit:
            add(explicit.group(1))
            continue

        cleaned = line.strip().lstrip("-*").strip()
        add(normalize_video_id(cleaned))

    return video_ids


def as_jsonable(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return as_jsonable(dataclasses.asdict(value))
    if hasattr(value, "model_dump"):
        return as_jsonable(value.model_dump())
    if hasattr(value, "dict"):
        return as_jsonable(value.dict())
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "__dict__"):
        return as_jsonable(vars(value))
    return str(value)


def extract_text(data: Any) -> str:
    if isinstance(data, str):
        return data.strip()

    if isinstance(data, dict):
        for key in ("text", "transcript", "content", "body"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        for key in ("segments", "items", "chunks", "utterances", "results"):
            value = data.get(key)
            if isinstance(value, list):
                parts = []
                for item in value:
                    if isinstance(item, str):
                        parts.append(item.strip())
                    elif isinstance(item, dict):
                        text = item.get("text") or item.get("content")
                        if isinstance(text, str):
                            parts.append(text.strip())
                joined = "\n".join(part for part in parts if part)
                if joined.strip():
                    return joined.strip()

    found: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            text_value = value.get("text")
            if isinstance(text_value, str) and text_value.strip():
                found.append(text_value.strip())
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(data)
    return "\n".join(dict.fromkeys(found)).strip()


def markdown_for_transcript(
    *,
    video_id: str,
    source_url: str,
    lang: str,
    mode: str,
    fetched_at: str,
    result: Any,
) -> str:
    jsonable = as_jsonable(result)
    transcript_text = extract_text(jsonable)
    raw_json = json.dumps(jsonable, ensure_ascii=False, indent=2)
    fence = chr(96) * 3

    if not transcript_text:
        transcript_text = "_No transcript text could be extracted from the Supadata response._"

    return f"""---
video_id: {video_id}
source_url: {source_url}
provider: supadata
language_requested: {lang}
mode: {mode}
fetched_at: {fetched_at}
---

# Raw Transcript - {video_id}

## Source

- Video ID: {video_id}
- YouTube URL: {source_url}
- Transcript provider: Supadata
- Language requested: {lang}
- Mode: {mode}
- Fetched at: {fetched_at}

## Transcript Text

{transcript_text}

## Raw Supadata Result

{fence}json
{raw_json}
{fence}
"""


def fetch_one(client: Any, video_id: str, lang: str, mode: str) -> Any:
    url = f"https://www.youtube.com/watch?v={video_id}"
    return client.transcript(url=url, lang=lang, mode=mode)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch YouTube transcripts from Supadata into kb/sources/raw/<videoID>.md."
    )
    parser.add_argument("input_path", type=Path, help="Text/markdown file containing YouTube URLs or video IDs.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory for transcript markdown files.")
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE, help="File containing SUPADATA_API_KEY.")
    parser.add_argument("--lang", default="iw", help="Language passed to Supadata. Default: iw.")
    parser.add_argument("--mode", default="auto", help="Mode passed to Supadata. Default: auto.")
    parser.add_argument("--limit", type=int, default=None, help="Fetch only the first N parsed videos.")
    parser.add_argument("--sleep", type=float, default=0.0, help="Seconds to sleep between API requests.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing <videoID>.md files.")
    parser.add_argument("--dry-run", action="store_true", help="Parse and print video IDs without calling Supadata.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = args.input_path.expanduser()
    output_dir = args.output_dir.expanduser()
    env_file = args.env_file.expanduser()

    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 2

    video_ids = extract_video_ids(input_path)
    if args.limit is not None:
        video_ids = video_ids[: args.limit]

    if not video_ids:
        print(f"No YouTube video IDs found in {input_path}", file=sys.stderr)
        return 2

    print(f"Input: {input_path}")
    print(f"Videos parsed: {len(video_ids)}")

    if args.dry_run:
        for video_id in video_ids:
            print(video_id)
        return 0

    try:
        from supadata import Supadata
    except ImportError:
        print(
            "Missing Python package: supadata. Install it with: python3 -m pip install supadata",
            file=sys.stderr,
        )
        return 2

    load_env_file(env_file)
    api_key = os.environ.get("SUPADATA_API_KEY") or os.environ.get("SUPADATA_KEY")
    if not api_key:
        print(f"Missing SUPADATA_API_KEY. Expected it in {env_file} or the environment.", file=sys.stderr)
        return 2

    output_dir.mkdir(parents=True, exist_ok=True)
    client = Supadata(api_key=api_key)

    fetched = 0
    skipped = 0
    failed = 0

    for index, video_id in enumerate(video_ids, start=1):
        output_path = output_dir / f"{video_id}.md"
        if output_path.exists() and not args.force:
            skipped += 1
            print(f"[{index}/{len(video_ids)}] skip existing {output_path}")
            continue

        source_url = f"https://www.youtube.com/watch?v={video_id}"
        print(f"[{index}/{len(video_ids)}] fetch {video_id}")

        try:
            result = fetch_one(client, video_id, args.lang, args.mode)
            fetched_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
            markdown = markdown_for_transcript(
                video_id=video_id,
                source_url=source_url,
                lang=args.lang,
                mode=args.mode,
                fetched_at=fetched_at,
                result=result,
            )
            output_path.write_text(markdown, encoding="utf-8")
            fetched += 1
            print(f"[{index}/{len(video_ids)}] wrote {output_path}")
        except Exception as exc:
            failed += 1
            print(f"[{index}/{len(video_ids)}] failed {video_id}: {type(exc).__name__}: {exc}", file=sys.stderr)

        if args.sleep and index < len(video_ids):
            time.sleep(args.sleep)

    print(f"Done. fetched={fetched} skipped={skipped} failed={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
