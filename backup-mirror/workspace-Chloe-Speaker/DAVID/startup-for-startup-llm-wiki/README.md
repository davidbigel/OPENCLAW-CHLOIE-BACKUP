# Startup for Startup LLM Wiki

Runnable local Python pipeline for turning .md and .txt podcast transcripts into an Obsidian-ready wiki.

## What it does

- stages raw transcripts without overwriting the originals
- normalizes transcript text and keeps source traceability
- chunks the text into stable artifacts
- builds topic, speaker, concept, quote, and cross-reference indexes
- generates wiki pages for episodes, people, themes, and concepts
- exports a clean Obsidian vault
- writes QA and run reports

## Layout

The pipeline writes its outputs into these folders under --root:

- 00_inbox/
- 01_normalized/
- 02_chunks/
- 03_index/
- 04_wiki/
- 05_obsidian_export/
- 06_reports/

## Install

From this folder:

    python -m pip install -e .

## Run

Point the pipeline at a folder containing transcript .md and .txt files:

    startup-wiki run --root /path/to/workspace --input /path/to/transcripts

Run individual steps if you want to inspect intermediate artifacts:

    startup-wiki ingest --root /path/to/workspace --input /path/to/transcripts
    startup-wiki normalize --root /path/to/workspace
    startup-wiki chunk --root /path/to/workspace
    startup-wiki index --root /path/to/workspace
    startup-wiki wiki --root /path/to/workspace
    startup-wiki export --root /path/to/workspace
    startup-wiki report --root /path/to/workspace

## Testing

    pytest

## Notes

- The app is dependency-light and uses only the Python standard library.
- If your transcripts have richer metadata, extend the normalization parser in src/startup_wiki/pipeline.py.
- The generated Obsidian vault lives in 05_obsidian_export/.
