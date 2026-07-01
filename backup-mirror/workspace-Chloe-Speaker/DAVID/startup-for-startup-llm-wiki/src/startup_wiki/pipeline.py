from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import re
import shutil

from .models import Chunk, NormalizedTranscript, PipelineStats, SourceFile, TranscriptMetadata, WikiPage
from .utils import (
    checksum_bytes,
    checksum_text,
    ensure_dir,
    extract_capitalized_phrases,
    extract_quotes,
    extract_title,
    json_dump,
    json_load,
    normalize_whitespace,
    parse_frontmatter,
    rel_path,
    render_frontmatter,
    sentence_split,
    slugify,
    stable_hash,
    top_keywords,
    unique_sorted,
)


class Pipeline:
    def __init__(self, root: Path):
        self.root = root
        self.inbox = root / "00_inbox"
        self.normalized_dir = root / "01_normalized"
        self.chunks_dir = root / "02_chunks"
        self.index_dir = root / "03_index"
        self.wiki_dir = root / "04_wiki"
        self.export_dir = root / "05_obsidian_export"
        self.reports_dir = root / "06_reports"
        self.manifest_path = self.inbox / "manifest.json"
        self.normalized_manifest_path = self.normalized_dir / "manifest.json"
        self.chunk_manifest_path = self.chunks_dir / "manifest.json"
        self.workspace_dirs = [
            self.inbox,
            self.normalized_dir,
            self.chunks_dir,
            self.index_dir,
            self.wiki_dir,
            self.export_dir,
            self.reports_dir,
        ]

    def init_workspace(self) -> None:
        for path in self.workspace_dirs:
            ensure_dir(path)

    def discover_sources(self, input_dir: Path) -> list[Path]:
        if not input_dir.exists():
            return []
        files = [
            path
            for path in input_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in {".md", ".txt"}
        ]
        return sorted(files)

    def ingest(self, input_dir: Path) -> PipelineStats:
        self.init_workspace()
        stats = PipelineStats()
        sources = self.discover_sources(input_dir)
        stats.discovered = len(sources)
        manifest: list[dict[str, object]] = []
        seen_checksums: dict[str, str] = {}
        for index, source in enumerate(sources, start=1):
            data = source.read_bytes()
            checksum = checksum_bytes(data)
            file_type = source.suffix.lower().lstrip(".")
            staged_name = f"{index:04d}-{slugify(source.stem)}{source.suffix.lower()}"
            staged_path = self.inbox / "raw" / staged_name
            if checksum in seen_checksums:
                stats.skipped += 1
                stats.warnings.append(
                    f"duplicate source skipped: {source} matches {seen_checksums[checksum]}"
                )
                continue
            staged_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, staged_path)
            seen_checksums[checksum] = str(source)
            manifest.append(
                {
                    "source_path": str(source),
                    "staged_path": str(staged_path),
                    "checksum": checksum,
                    "size": len(data),
                    "discovered_name": source.name,
                    "file_type": file_type,
                }
            )
            stats.staged += 1
        json_dump(self.manifest_path, manifest)
        return stats

    def load_manifest(self) -> list[SourceFile]:
        if not self.manifest_path.exists():
            return []
        raw = json_load(self.manifest_path)
        assert isinstance(raw, list)
        return [
            SourceFile(
                source_path=Path(item["source_path"]),
                staged_path=Path(item["staged_path"]),
                checksum=item["checksum"],
                size=item["size"],
                discovered_name=item["discovered_name"],
                file_type=item["file_type"],
            )
            for item in raw
        ]

    def normalize(self) -> list[NormalizedTranscript]:
        self.init_workspace()
        outputs: list[NormalizedTranscript] = []
        manifest = self.load_manifest()
        normalized_manifest: list[dict[str, object]] = []
        for source in manifest:
            staged_text = source.staged_path.read_text(encoding="utf-8", errors="replace")
            metadata, body = parse_frontmatter(staged_text)
            cleaned = normalize_whitespace(body if metadata else staged_text)
            title = metadata.get("title") or extract_title(body if metadata else staged_text, source.staged_path.stem)
            transcript_id = stable_hash(str(source.source_path), source.checksum, title, length=12)
            slug_source = metadata.get("slug") or metadata.get("youtube_id") or title or source.staged_path.stem
            slug = slugify(str(slug_source))
            speakers = unique_sorted(self._extract_speakers(cleaned))
            normalized_metadata = TranscriptMetadata(
                transcript_id=transcript_id,
                title=title,
                slug=slug,
                source_path=str(source.source_path),
                checksum=source.checksum,
                file_type=source.file_type,
                episode_date=metadata.get("date") or metadata.get("episode_date"),
                speakers=speakers,
                tags=unique_sorted(self._parse_csv(metadata.get("tags", ""))),
                extra={
                    k: v
                    for k, v in metadata.items()
                    if k not in {"title", "episode", "name", "date", "episode_date", "tags"}
                },
            )
            normalized_dir = self.normalized_dir / slug[:1] / slug
            normalized_dir.mkdir(parents=True, exist_ok=True)
            normalized_path = normalized_dir / f"{slug}.md"
            rendered = self._render_normalized_markdown(normalized_metadata, cleaned)
            normalized_path.write_text(rendered, encoding="utf-8")
            outputs.append(
                NormalizedTranscript(
                    metadata=normalized_metadata,
                    text=cleaned,
                    source_relpath=rel_path(self.root, source.staged_path),
                    normalized_path=normalized_path,
                )
            )
            normalized_manifest.append(
                {
                    "metadata": asdict(normalized_metadata),
                    "normalized_path": str(normalized_path),
                    "source_relpath": rel_path(self.root, source.staged_path),
                }
            )
        json_dump(self.normalized_manifest_path, normalized_manifest)
        return outputs

    def load_normalized(self) -> list[NormalizedTranscript]:
        if not self.normalized_manifest_path.exists():
            return []
        raw = json_load(self.normalized_manifest_path)
        assert isinstance(raw, list)
        outputs: list[NormalizedTranscript] = []
        for item in raw:
            md = item["metadata"]
            metadata = TranscriptMetadata(
                transcript_id=md["transcript_id"],
                title=md["title"],
                slug=md["slug"],
                source_path=md["source_path"],
                checksum=md["checksum"],
                file_type=md["file_type"],
                episode_date=md.get("episode_date"),
                speakers=list(md.get("speakers", [])),
                tags=list(md.get("tags", [])),
                extra=dict(md.get("extra", {})),
            )
            normalized_path = Path(item["normalized_path"])
            text = normalized_path.read_text(encoding="utf-8")
            _, body = parse_frontmatter(text)
            outputs.append(
                NormalizedTranscript(
                    metadata=metadata,
                    text=body.strip(),
                    source_relpath=item["source_relpath"],
                    normalized_path=normalized_path,
                )
            )
        return outputs

    def chunk(self) -> list[Chunk]:
        self.init_workspace()
        transcripts = self.load_normalized()
        chunks: list[Chunk] = []
        manifest: list[dict[str, object]] = []
        for transcript in transcripts:
            transcript_chunks = self._chunk_transcript(transcript)
            chunks.extend(transcript_chunks)
            for chunk in transcript_chunks:
                chunk_path = self.chunks_dir / chunk.episode_slug / f"{chunk.order:03d}-{chunk.chunk_id}.json"
                chunk_path.parent.mkdir(parents=True, exist_ok=True)
                json_dump(chunk_path, asdict(chunk))
                manifest.append({"chunk_path": str(chunk_path), **asdict(chunk)})
        json_dump(self.chunk_manifest_path, manifest)
        return chunks

    def load_chunks(self) -> list[Chunk]:
        if not self.chunk_manifest_path.exists():
            return []
        raw = json_load(self.chunk_manifest_path)
        assert isinstance(raw, list)
        return [Chunk(**item) for item in raw]

    def build_indexes(self) -> dict[str, Path]:
        self.init_workspace()
        transcripts = self.load_normalized()
        chunks = self.load_chunks()
        if not transcripts and not chunks:
            return {}
        episode_index = self._build_episode_index(transcripts, chunks)
        speaker_index = self._build_speaker_index(transcripts, chunks)
        topic_index = self._build_topic_index(chunks)
        concept_index = self._build_concept_index(chunks)
        quote_index = self._build_quote_index(chunks)
        xref_index = self._build_xref_index(episode_index, speaker_index, topic_index, concept_index, quote_index)
        outputs = {
            "episode_index": self.index_dir / "episode_index.json",
            "speaker_index": self.index_dir / "speaker_index.json",
            "topic_index": self.index_dir / "topic_index.json",
            "concept_index": self.index_dir / "concept_index.json",
            "quote_index": self.index_dir / "quote_index.json",
            "xref_index": self.index_dir / "cross_reference_index.json",
        }
        json_dump(outputs["episode_index"], episode_index)
        json_dump(outputs["speaker_index"], speaker_index)
        json_dump(outputs["topic_index"], topic_index)
        json_dump(outputs["concept_index"], concept_index)
        json_dump(outputs["quote_index"], quote_index)
        json_dump(outputs["xref_index"], xref_index)
        return outputs

    def generate_wiki(self) -> list[WikiPage]:
        self.init_workspace()
        transcripts = self.load_normalized()
        chunks = self.load_chunks()
        pages: list[WikiPage] = []
        pages.extend(self._generate_episode_pages(transcripts, chunks))
        pages.extend(self._generate_people_pages(transcripts, chunks))
        pages.extend(self._generate_theme_pages(chunks))
        pages.extend(self._generate_concept_pages(chunks))
        pages.extend(self._generate_index_pages())
        for page in pages:
            page.path.parent.mkdir(parents=True, exist_ok=True)
            page.path.write_text(page.body, encoding="utf-8")
        manifest = [
            {
                "page_id": page.page_id,
                "title": page.title,
                "page_type": page.page_type,
                "path": str(page.path),
                "frontmatter": page.frontmatter,
            }
            for page in pages
        ]
        json_dump(self.wiki_dir / "manifest.json", manifest)
        return pages

    def export_obsidian(self) -> list[Path]:
        self.init_workspace()
        if self.export_dir.exists():
            shutil.rmtree(self.export_dir)
        ensure_dir(self.export_dir)
        copied: list[Path] = []
        for source in self.wiki_dir.rglob("*.md"):
            rel = source.relative_to(self.wiki_dir)
            target = self.export_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied.append(target)
        for source in self.index_dir.rglob("*.json"):
            target = self.export_dir / "Indexes" / source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied.append(target)
        copied.append(self._write_vault_readme())
        return copied

    def write_reports(self) -> dict[str, Path]:
        self.init_workspace()
        qa = self._build_qa_report()
        run = self._build_run_report(qa)
        qa_path = self.reports_dir / "qa_report.md"
        run_path = self.reports_dir / "run_report.md"
        qa_path.write_text(qa, encoding="utf-8")
        run_path.write_text(run, encoding="utf-8")
        return {"qa": qa_path, "run": run_path}

    def run_all(self, input_dir: Path) -> dict[str, object]:
        self.init_workspace()
        ingest_stats = self.ingest(input_dir)
        normalized = self.normalize()
        chunks = self.chunk()
        indexes = self.build_indexes()
        wiki_pages = self.generate_wiki()
        exported = self.export_obsidian()
        reports = self.write_reports()
        return {
            "ingest": ingest_stats,
            "normalized": len(normalized),
            "chunks": len(chunks),
            "indexes": {name: str(path) for name, path in indexes.items()},
            "wiki_pages": len(wiki_pages),
            "exported": len(exported),
            "reports": {name: str(path) for name, path in reports.items()},
        }

    def _extract_speakers(self, text: str) -> list[str]:
        speakers: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if ":" in stripped:
                speaker = stripped.split(":", 1)[0].strip()
                if 1 < len(speaker) <= 60 and speaker[0].isalpha() and speaker[0].isupper():
                    speakers.append(speaker)
        return speakers

    def _parse_csv(self, value: object) -> list[str]:
        if not value:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return [item.strip() for item in str(value).split(",") if item.strip()]

    def _render_normalized_markdown(self, metadata: TranscriptMetadata, body: str) -> str:
        frontmatter = {
            "type": "normalized_transcript",
            "transcript_id": metadata.transcript_id,
            "title": metadata.title,
            "slug": metadata.slug,
            "source_path": metadata.source_path,
            "checksum": metadata.checksum,
            "file_type": metadata.file_type,
            "episode_date": metadata.episode_date,
            "speakers": metadata.speakers,
            "tags": metadata.tags,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        if metadata.extra:
            frontmatter["extra"] = metadata.extra
        return render_frontmatter(frontmatter) + "\n\n" + body.strip() + "\n"

    def _split_segments(self, text: str) -> list[str]:
        segments: list[str] = []
        buffer: list[str] = []
        for line in text.splitlines():
            if not line.strip():
                if buffer:
                    segments.append("\n".join(buffer).strip())
                    buffer = []
                continue
            if line.startswith("#") and buffer:
                segments.append("\n".join(buffer).strip())
                buffer = [line]
                continue
            if buffer and re.match(r"^[A-Za-z][A-Za-z0-9 .,'&()/\-]{0,60}:\s+.+$", line.strip()):
                segments.append("\n".join(buffer).strip())
                buffer = [line]
                continue
            buffer.append(line)
        if buffer:
            segments.append("\n".join(buffer).strip())
        return [segment for segment in segments if segment]

    def _chunk_transcript(self, transcript: NormalizedTranscript, target_chars: int = 1400, overlap_chars: int = 180) -> list[Chunk]:
        segments = self._split_segments(transcript.text)
        if not segments:
            return []
        chunks: list[Chunk] = []
        current: list[str] = []
        current_len = 0
        order = 1
        start_segment = 1
        for idx, segment in enumerate(segments, start=1):
            if current and current_len + len(segment) > target_chars:
                chunk_text = "\n\n".join(current).strip()
                chunks.append(self._build_chunk(transcript, order, chunk_text, start_segment, idx - 1))
                order += 1
                overlap = self._overlap_segments(current, overlap_chars)
                current = overlap[:] if overlap else []
                current_len = sum(len(part) for part in current)
                start_segment = max(1, idx - len(current))
            current.append(segment)
            current_len += len(segment)
        if current:
            chunk_text = "\n\n".join(current).strip()
            chunks.append(self._build_chunk(transcript, order, chunk_text, start_segment, len(segments)))
        return chunks

    def _overlap_segments(self, segments: list[str], overlap_chars: int) -> list[str]:
        if not segments:
            return []
        carried: list[str] = []
        total = 0
        for segment in reversed(segments):
            if total + len(segment) > overlap_chars and carried:
                break
            carried.append(segment)
            total += len(segment)
        return list(reversed(carried))

    def _build_chunk(
        self,
        transcript: NormalizedTranscript,
        order: int,
        text: str,
        start_segment: int,
        end_segment: int,
    ) -> Chunk:
        topics = [word for word, _ in top_keywords([text], limit=5)]
        concepts = extract_capitalized_phrases(text, limit=5)
        quote = next(iter(extract_quotes(text, limit=1)), None)
        speaker = transcript.metadata.speakers[0] if transcript.metadata.speakers else None
        first_sentence = sentence_split(text)[0] if sentence_split(text) else transcript.metadata.title
        chunk_id = f"{transcript.metadata.slug}-{order:03d}-{stable_hash(transcript.metadata.transcript_id, str(order), text, length=8)}"
        return Chunk(
            chunk_id=chunk_id,
            transcript_id=transcript.metadata.transcript_id,
            episode_slug=transcript.metadata.slug,
            order=order,
            text=text,
            title=first_sentence[:120],
            speaker=speaker,
            section=None,
            source_path=transcript.source_relpath,
            checksum=checksum_text(text),
            start_segment=start_segment,
            end_segment=end_segment,
            topics=topics,
            concepts=concepts,
            quote=quote,
        )

    def _build_episode_index(self, transcripts: list[NormalizedTranscript], chunks: list[Chunk]) -> dict[str, object]:
        chunk_count_by_id: dict[str, int] = {}
        for chunk in chunks:
            chunk_count_by_id[chunk.transcript_id] = chunk_count_by_id.get(chunk.transcript_id, 0) + 1
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "episodes": [
                {
                    "transcript_id": item.metadata.transcript_id,
                    "title": item.metadata.title,
                    "slug": item.metadata.slug,
                    "source_path": item.metadata.source_path,
                    "checksum": item.metadata.checksum,
                    "file_type": item.metadata.file_type,
                    "speakers": item.metadata.speakers,
                    "tags": item.metadata.tags,
                    "chunk_count": chunk_count_by_id.get(item.metadata.transcript_id, 0),
                }
                for item in transcripts
            ],
        }

    def _build_speaker_index(self, transcripts: list[NormalizedTranscript], chunks: list[Chunk]) -> dict[str, object]:
        mapping: dict[str, dict[str, object]] = {}
        for transcript in transcripts:
            for speaker in transcript.metadata.speakers:
                mapping.setdefault(speaker, {"speaker": speaker, "episodes": set(), "chunks": set(), "mentions": 0})
                mapping[speaker]["episodes"].add(transcript.metadata.slug)
        for chunk in chunks:
            if chunk.speaker:
                entry = mapping.setdefault(chunk.speaker, {"speaker": chunk.speaker, "episodes": set(), "chunks": set(), "mentions": 0})
                entry["chunks"].add(chunk.chunk_id)
                entry["mentions"] += 1
                entry["episodes"].add(chunk.episode_slug)
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "speakers": [
                {
                    "speaker": speaker,
                    "episodes": sorted(entry["episodes"]),
                    "chunks": sorted(entry["chunks"]),
                    "mentions": entry["mentions"],
                }
                for speaker, entry in sorted(mapping.items())
            ],
        }

    def _build_topic_index(self, chunks: list[Chunk]) -> dict[str, object]:
        texts = [chunk.text for chunk in chunks]
        keywords = top_keywords(texts, limit=50)
        topics = []
        for topic, count in keywords:
            refs = [chunk.chunk_id for chunk in chunks if topic in chunk.topics]
            if refs:
                topics.append(
                    {
                        "topic": topic,
                        "count": count,
                        "chunk_ids": refs[:25],
                        "episodes": sorted({chunk.episode_slug for chunk in chunks if topic in chunk.topics}),
                    }
                )
        return {"generated_at": datetime.now(timezone.utc).isoformat(), "topics": topics}

    def _build_concept_index(self, chunks: list[Chunk]) -> dict[str, object]:
        concept_map: dict[str, dict[str, object]] = {}
        for chunk in chunks:
            for concept in chunk.concepts:
                key = concept.lower()
                entry = concept_map.setdefault(key, {"concept": concept, "chunk_ids": set(), "episodes": set(), "mentions": 0})
                entry["chunk_ids"].add(chunk.chunk_id)
                entry["episodes"].add(chunk.episode_slug)
                entry["mentions"] += 1
        concepts = [
            {
                "concept": entry["concept"],
                "chunk_ids": sorted(entry["chunk_ids"]),
                "episodes": sorted(entry["episodes"]),
                "mentions": entry["mentions"],
            }
            for key, entry in sorted(concept_map.items(), key=lambda item: (-item[1]["mentions"], item[0]))
            if entry["mentions"] >= 2
        ]
        return {"generated_at": datetime.now(timezone.utc).isoformat(), "concepts": concepts[:100]}

    def _build_quote_index(self, chunks: list[Chunk]) -> dict[str, object]:
        quotes = []
        for chunk in chunks:
            if chunk.quote:
                quotes.append(
                    {
                        "quote": chunk.quote,
                        "chunk_id": chunk.chunk_id,
                        "episode_slug": chunk.episode_slug,
                        "title": chunk.title,
                    }
                )
        return {"generated_at": datetime.now(timezone.utc).isoformat(), "quotes": quotes[:200]}

    def _build_xref_index(self, *indexes: dict[str, object]) -> dict[str, object]:
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "index_names": ["episode_index", "speaker_index", "topic_index", "concept_index", "quote_index"],
            "reference_count": sum(len(index) for index in indexes),
        }

    def _page_path(self, folder: str, title: str, slug_hint: str | None = None) -> Path:
        return self.wiki_dir / folder / f"{slugify(slug_hint or title)}.md"

    def _generate_episode_pages(self, transcripts: list[NormalizedTranscript], chunks: list[Chunk]) -> list[WikiPage]:
        pages: list[WikiPage] = []
        chunk_map: dict[str, list[Chunk]] = {}
        for chunk in chunks:
            chunk_map.setdefault(chunk.transcript_id, []).append(chunk)
        for transcript in transcripts:
            episode_chunks = chunk_map.get(transcript.metadata.transcript_id, [])
            related_topics = unique_sorted([topic for chunk in episode_chunks for topic in chunk.topics])[:8]
            related_concepts = unique_sorted([concept for chunk in episode_chunks for concept in chunk.concepts])[:8]
            page_title = transcript.metadata.title
            body = self._render_page(
                page_title,
                "episode",
                {
                    "transcript_id": transcript.metadata.transcript_id,
                    "source_path": transcript.metadata.source_path,
                    "checksum": transcript.metadata.checksum,
                    "speakers": transcript.metadata.speakers,
                    "tags": transcript.metadata.tags,
                    "chunk_count": len(episode_chunks),
                },
                summary=self._episode_summary(transcript, episode_chunks),
                key_points=self._episode_key_points(episode_chunks),
                related=[("Topics", title) for title in related_topics] + [("Concepts", title) for title in related_concepts],
                source_refs=[f"{chunk.chunk_id} -> {chunk.source_path}" for chunk in episode_chunks[:8]],
            )
            pages.append(
                WikiPage(
                    page_id=transcript.metadata.transcript_id,
                    title=page_title,
                    page_type="episode",
                    path=self._page_path("Episodes", page_title, transcript.metadata.slug),
                    body=body,
                    frontmatter={"type": "episode", "title": page_title, "transcript_id": transcript.metadata.transcript_id},
                )
            )
        return pages

    def _generate_people_pages(self, transcripts: list[NormalizedTranscript], chunks: list[Chunk]) -> list[WikiPage]:
        people: dict[str, dict[str, object]] = {}
        for transcript in transcripts:
            for speaker in transcript.metadata.speakers:
                people.setdefault(speaker, {"episodes": set(), "chunks": set(), "mentions": 0})
                people[speaker]["episodes"].add(transcript.metadata.slug)
        for chunk in chunks:
            if chunk.speaker:
                entry = people.setdefault(chunk.speaker, {"episodes": set(), "chunks": set(), "mentions": 0})
                entry["episodes"].add(chunk.episode_slug)
                entry["chunks"].add(chunk.chunk_id)
                entry["mentions"] += 1
        pages: list[WikiPage] = []
        for person, entry in sorted(people.items()):
            body = self._render_page(
                person,
                "person",
                {"mentions": entry["mentions"]},
                summary=f"{person} appears in {len(entry['episodes'])} episode(s) and {entry['mentions']} chunk(s).",
                key_points=[
                    f"Appears in episodes: {', '.join(sorted(entry['episodes'])[:8])}",
                    f"Chunk references: {', '.join(sorted(entry['chunks'])[:8])}",
                ],
                related=[("Episodes", episode) for episode in sorted(entry["episodes"])[:8]],
                source_refs=sorted(entry["chunks"])[:8],
            )
            pages.append(
                WikiPage(
                    page_id=slugify(person),
                    title=person,
                    page_type="person",
                    path=self._page_path("People", person),
                    body=body,
                    frontmatter={"type": "person", "title": person},
                )
            )
        return pages

    def _generate_theme_pages(self, chunks: list[Chunk]) -> list[WikiPage]:
        topic_index = self._build_topic_index(chunks)
        pages: list[WikiPage] = []
        for item in topic_index["topics"][:50]:
            title = item["topic"].title()
            body = self._render_page(
                title,
                "theme",
                {"mentions": item["count"]},
                summary=f"Theme page for {item['topic']} across {len(item['episodes'])} episode(s).",
                key_points=[
                    f"Referenced in episodes: {', '.join(item['episodes'][:8])}",
                    f"Chunk ids: {', '.join(item['chunk_ids'][:8])}",
                ],
                related=[("Episodes", episode) for episode in item["episodes"][:5]],
                source_refs=item["chunk_ids"][:5],
            )
            pages.append(
                WikiPage(
                    page_id=slugify(title),
                    title=title,
                    page_type="theme",
                    path=self._page_path("Themes", title),
                    body=body,
                    frontmatter={"type": "theme", "title": title},
                )
            )
        return pages

    def _generate_concept_pages(self, chunks: list[Chunk]) -> list[WikiPage]:
        concept_index = self._build_concept_index(chunks)
        pages: list[WikiPage] = []
        for item in concept_index["concepts"][:50]:
            title = item["concept"]
            body = self._render_page(
                title,
                "concept",
                {"mentions": item["mentions"]},
                summary=f"Concept page for {title} across {len(item['episodes'])} episode(s).",
                key_points=[
                    f"Referenced in episodes: {', '.join(item['episodes'][:8])}",
                    f"Chunk ids: {', '.join(item['chunk_ids'][:8])}",
                ],
                related=[("Episodes", episode) for episode in item["episodes"][:5]],
                source_refs=item["chunk_ids"][:5],
            )
            pages.append(
                WikiPage(
                    page_id=slugify(title),
                    title=title,
                    page_type="concept",
                    path=self._page_path("Concepts", title),
                    body=body,
                    frontmatter={"type": "concept", "title": title},
                )
            )
        return pages

    def _generate_index_pages(self) -> list[WikiPage]:
        index_files = sorted(self.index_dir.glob("*.json"))
        pages: list[WikiPage] = []
        if not index_files:
            return pages
        body = self._render_page(
            "Indexes",
            "index",
            {"files": [path.name for path in index_files]},
            summary="Entry point for generated indexes.",
            key_points=[f"Available files: {', '.join(path.name for path in index_files)}"],
            related=[],
            source_refs=[path.stem for path in index_files],
        )
        pages.append(
            WikiPage(
                page_id="indexes",
                title="Indexes",
                page_type="index",
                path=self._page_path("", "Indexes"),
                body=body,
                frontmatter={"type": "index", "title": "Indexes"},
            )
        )
        return pages

    def _render_page(
        self,
        title: str,
        page_type: str,
        extra_frontmatter: dict[str, object],
        summary: str,
        key_points: list[str],
        related: list[tuple[str, str]],
        source_refs: list[str],
    ) -> str:
        frontmatter = {
            "type": page_type,
            "title": title,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        frontmatter.update(extra_frontmatter)
        lines = [
            render_frontmatter(frontmatter),
            "",
            f"# {title}",
            "",
            "## Summary",
            summary,
            "",
            "## Key Points",
        ]
        if key_points:
            lines.extend(f"- {point}" for point in key_points)
        else:
            lines.append("- No key points available.")
        if related:
            lines.extend(["", "## Related"])
            lines.extend(f"- {label}: [[{target}]]" for label, target in self._dedupe_related(related))
        if source_refs:
            lines.extend(["", "## Source References"])
            lines.extend(f"- {ref}" for ref in source_refs)
        return "\n".join(lines).strip() + "\n"

    def _dedupe_related(self, related: list[tuple[str, str]]) -> list[tuple[str, str]]:
        seen: set[str] = set()
        output: list[tuple[str, str]] = []
        for label, target in related:
            key = target.lower()
            if key not in seen:
                seen.add(key)
                output.append((label, target))
        return output

    def _episode_summary(self, transcript: NormalizedTranscript, episode_chunks: list[Chunk]) -> str:
        excerpt = " ".join(sentence_split(transcript.text)[:2])
        if not excerpt:
            excerpt = transcript.metadata.title
        return f"{transcript.metadata.title} contains {len(episode_chunks)} chunk(s). {excerpt[:240]}"

    def _episode_key_points(self, episode_chunks: list[Chunk]) -> list[str]:
        topics = unique_sorted([topic for chunk in episode_chunks for topic in chunk.topics])[:6]
        concepts = unique_sorted([concept for chunk in episode_chunks for concept in chunk.concepts])[:6]
        key_points = []
        if topics:
            key_points.append(f"Topics: {', '.join(topics)}")
        if concepts:
            key_points.append(f"Concepts: {', '.join(concepts)}")
        for chunk in episode_chunks[:3]:
            key_points.append(f"{chunk.chunk_id}: {chunk.title}")
        return key_points

    def _write_vault_readme(self) -> Path:
        readme = self.export_dir / "README.md"
        readme.write_text(
            "# Startup for Startup Wiki Vault\n\n"
            "Open this folder in Obsidian. Generated wiki pages live in the subfolders below.\n\n"
            "- Episodes\n- People\n- Themes\n- Concepts\n- Indexes\n",
            encoding="utf-8",
        )
        return readme

    def _build_qa_report(self) -> str:
        normalized = self.load_normalized()
        chunks = self.load_chunks()
        index_files = sorted(self.index_dir.glob("*.json"))
        wiki_files = sorted(self.wiki_dir.rglob("*.md"))
        broken_links: list[str] = []
        available_targets = {path.stem for path in wiki_files}
        for page in wiki_files:
            text = page.read_text(encoding="utf-8")
            for match in set(re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", text)):
                if slugify(match) not in available_targets and match not in available_targets:
                    broken_links.append(f"{page.relative_to(self.root)} -> {match}")
        duplicates = self._find_duplicate_pages(wiki_files)
        lines = [
            "# QA Report",
            "",
            f"- normalized transcripts: {len(normalized)}",
            f"- chunks: {len(chunks)}",
            f"- wiki pages: {len(wiki_files)}",
            f"- index files: {len(index_files)}",
            f"- broken links: {len(broken_links)}",
            f"- duplicate pages: {len(duplicates)}",
            "",
            "## Broken Links",
        ]
        if broken_links:
            lines.extend(f"- {item}" for item in broken_links)
        else:
            lines.append("- None found.")
        lines.extend(["", "## Duplicate Pages"])
        if duplicates:
            lines.extend(f"- {item}" for item in duplicates)
        else:
            lines.append("- None found.")
        lines.extend(["", "## Skipped or Blocked", "- See ingest warnings and report notes in the run report."])
        return "\n".join(lines).strip() + "\n"

    def _build_run_report(self, qa_report: str) -> str:
        normalized = self.load_normalized()
        chunks = self.load_chunks()
        pages = sorted(self.wiki_dir.rglob("*.md"))
        blockers = []
        if not normalized:
            blockers.append("No normalized transcripts were produced.")
        if not chunks:
            blockers.append("No chunks were produced.")
        confidence = "high" if normalized and chunks and pages else "medium" if normalized or chunks else "low"
        recommendations = [
            "Point the ingest command at the full transcript corpus.",
            "Review theme/concept pages for threshold tuning if the corpus is large.",
            "Add transcript-specific metadata parsing if the source archive has richer headers.",
        ]
        return (
            "# Run Report\n\n"
            f"- confidence: {confidence}\n"
            f"- normalized transcripts: {len(normalized)}\n"
            f"- chunks: {len(chunks)}\n"
            f"- wiki pages: {len(pages)}\n"
            f"- blockers: {', '.join(blockers) if blockers else 'none'}\n\n"
            "## Next Steps\n"
            + "\n".join(f"- {item}" for item in recommendations)
            + "\n\n## QA Snapshot\n"
            + qa_report
        )

    def _find_duplicate_pages(self, wiki_files: list[Path]) -> list[str]:
        by_hash: dict[str, list[str]] = {}
        for path in wiki_files:
            body = path.read_text(encoding="utf-8")
            digest = checksum_text(body)
            by_hash.setdefault(digest, []).append(str(path.relative_to(self.root)))
        duplicates = []
        for paths in by_hash.values():
            if len(paths) > 1:
                duplicates.append(", ".join(paths))
        return duplicates
