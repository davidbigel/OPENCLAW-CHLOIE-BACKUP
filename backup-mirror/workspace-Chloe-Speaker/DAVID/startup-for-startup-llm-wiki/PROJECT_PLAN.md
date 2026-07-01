# Project Plan

## Objective

Build a wiki-grade LLM knowledge base from the full *Startup for Startup* transcript corpus, with clean exports into Obsidian.

## Desired end state

- All transcripts collected in a single controlled workspace
- Cleaned text normalized into a consistent format
- Sections, episodes, topics, and themes indexed
- Cross-links between related ideas and episodes
- Outputs rendered as Obsidian-ready markdown files
- A repeatable pipeline that can be rerun as new episodes arrive

## Recommended architecture

### 1. Workspace layout

Use a dedicated project root with clear separation between raw inputs, derived artifacts, and final exports:

- `00_inbox/` for raw transcripts and source dumps
- `01_normalized/` for cleaned text
- `02_chunks/` for chunk-level artifacts
- `03_index/` for topic and entity indexes
- `04_wiki/` for curated wiki pages
- `05_obsidian_export/` for Obsidian-ready markdown
- `06_reports/` for QA and run reports

### 2. Ingestion

Ingest transcript sources from the podcast archive into raw files without editing the originals.

Required checks:

- source completeness
- episode naming consistency
- transcript language detection
- duplicate detection

### 3. Normalization

Clean each transcript into a canonical representation:

- remove timestamps only if they are not needed downstream
- preserve speaker labels where available
- standardize punctuation and whitespace
- normalize episode metadata
- keep a reference back to the raw source

### 4. Chunking

Split transcripts into semantically meaningful chunks rather than fixed-size blind slices.

Chunking rules:

- prefer topic boundaries
- maintain local context overlap
- tag chunks with episode id, speaker, and section metadata
- keep chunk ids stable across reruns

### 5. Indexing

Build indexes that support retrieval and wiki navigation:

- episode index
- people index
- topic index
- concept index
- quote index
- linked references index

### 6. Wiki generation

Generate wiki pages for:

- each episode
- recurring themes
- people and organizations
- conceptual clusters
- strong quotes and examples

Each wiki page should include:

- short summary
- source links
- related pages
- key excerpts
- external notes if needed

### 7. Obsidian export

Export final markdown into an Obsidian-compatible folder structure.

Requirements:

- frontmatter with stable metadata
- internal links instead of fragile references where possible
- predictable file names
- readable markdown without tool-specific noise

### 8. Quality control

Add validation for:

- missing transcripts
- empty chunks
- duplicate pages
- broken links
- malformed metadata
- episode/article mismatch

### 9. Self-healing behavior

The worker should automatically:

- retry transient download failures
- skip and log irrecoverable episodes
- surface blockers clearly
- continue processing unaffected items

### 10. Deliverables

- a fully organized workspace
- a run report
- the one-shot implementation prompt
- a reproducible workflow description
- the export-ready wiki folder

## Execution strategy

1. Discover the source corpus.
2. Mirror raw data into the inbox.
3. Normalize transcript content.
4. Chunk and index.
5. Generate wiki pages.
6. Export to Obsidian.
7. Validate and report.

## Success criteria

The project is successful if:

- the corpus is fully represented
- wiki pages are navigable and linked
- exports are usable immediately in Obsidian
- the pipeline is repeatable
- the worker can run with minimal supervision
