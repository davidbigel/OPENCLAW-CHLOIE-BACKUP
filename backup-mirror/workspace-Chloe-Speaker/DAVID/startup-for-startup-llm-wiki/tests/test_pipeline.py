from __future__ import annotations

from pathlib import Path

from startup_wiki.pipeline import Pipeline
from startup_wiki.utils import normalize_whitespace, slugify


def write_sample_transcripts(input_dir: Path) -> None:
    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "episode-one.txt").write_text(
        "Episode: Building in Public\n\n"
        "Maya: We learned that distribution matters more than polish.\n"
        "Maya: Keep shipping and measure what users actually do.\n\n"
        "Ari: The product changed after the first ten customers.\n",
        encoding="utf-8",
    )
    (input_dir / "episode-two.md").write_text(
        "---\n"
        "title: Hiring at Speed\n"
        "date: 2024-02-01\n"
        "tags: hiring, operations\n"
        "---\n\n"
        "# Hiring at Speed\n\n"
        "Nina: Good hiring is mostly a systems problem.\n"
        "Nina: We need better feedback loops and clearer ownership.\n",
        encoding="utf-8",
    )


def test_normalize_whitespace_removes_extra_space_and_blank_runs() -> None:
    text = "A  B \n\n\nC\t \n"
    assert normalize_whitespace(text) == "A B\n\nC"


def test_slugify_is_stable_and_url_safe() -> None:
    assert slugify("Hiring at Speed!") == "hiring-at-speed"


def test_pipeline_end_to_end_creates_expected_artifacts(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    write_sample_transcripts(input_dir)
    pipeline = Pipeline(tmp_path / "workspace")

    ingest = pipeline.ingest(input_dir)
    assert ingest.staged == 2

    normalized = pipeline.normalize()
    assert len(normalized) == 2
    assert all(item.normalized_path.exists() for item in normalized)

    chunks = pipeline.chunk()
    assert chunks
    assert all(chunk.chunk_id for chunk in chunks)

    indexes = pipeline.build_indexes()
    assert indexes
    assert (tmp_path / "workspace" / "03_index" / "episode_index.json").exists()

    pages = pipeline.generate_wiki()
    assert pages
    assert any(page.page_type == "episode" for page in pages)

    exported = pipeline.export_obsidian()
    assert exported
    assert (tmp_path / "workspace" / "05_obsidian_export" / "README.md").exists()

    reports = pipeline.write_reports()
    assert reports["qa"].exists()
    assert reports["run"].exists()


def test_export_paths_are_predictable(tmp_path: Path) -> None:
    pipeline = Pipeline(tmp_path / "workspace")
    path = pipeline._page_path("People", "Maya Angelou")
    assert path.name == "maya-angelou.md"
    assert path.parent.name == "People"
