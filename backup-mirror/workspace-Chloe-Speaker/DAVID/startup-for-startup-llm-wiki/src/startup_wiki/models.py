from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class SourceFile:
    source_path: Path
    staged_path: Path
    checksum: str
    size: int
    discovered_name: str
    file_type: str


@dataclass(slots=True)
class TranscriptMetadata:
    transcript_id: str
    title: str
    slug: str
    source_path: str
    checksum: str
    file_type: str
    episode_date: str | None = None
    speakers: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    extra: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class NormalizedTranscript:
    metadata: TranscriptMetadata
    text: str
    source_relpath: str
    normalized_path: Path


@dataclass(slots=True)
class Chunk:
    chunk_id: str
    transcript_id: str
    episode_slug: str
    order: int
    text: str
    title: str
    speaker: str | None
    section: str
    source_path: str
    checksum: str
    start_segment: int
    end_segment: int
    chunk_path: str | None = None
    topics: list[str] = field(default_factory=list)
    concepts: list[str] = field(default_factory=list)
    quote: str | None = None


@dataclass(slots=True)
class WikiPage:
    page_id: str
    title: str
    page_type: str
    path: Path
    body: str
    frontmatter: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PipelineStats:
    discovered: int = 0
    staged: int = 0
    skipped: int = 0
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "discovered": self.discovered,
            "staged": self.staged,
            "skipped_count": self.skipped,
            "warnings": list(self.warnings),
        }


@dataclass(slots=True)
class PipelineReport:
    input_count: int = 0
    ingested_count: int = 0
    normalized_count: int = 0
    chunk_count: int = 0
    episode_page_count: int = 0
    topic_page_count: int = 0
    skipped: list[dict[str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "input_count": self.input_count,
            "ingested_count": self.ingested_count,
            "normalized_count": self.normalized_count,
            "chunk_count": self.chunk_count,
            "episode_page_count": self.episode_page_count,
            "topic_page_count": self.topic_page_count,
            "skipped": list(self.skipped),
            "warnings": list(self.warnings),
        }
