# One-Shot Prompt for the Builder

You are building a wiki-grade LLM knowledge base from the full *Startup for Startup* podcast transcript corpus.

## Mission

Create a complete, Obsidian-ready knowledge base from the transcripts. The result should feel like a structured internal wiki, not just a pile of summaries.

## Important constraints

- Work autonomously.
- Do not ask for frequent clarification.
- If a tool or dependency is missing, discover a fallback and continue.
- Preserve raw inputs separately from derived outputs.
- Keep everything organized in a new project folder.
- Make the final export immediately usable in Obsidian.

## Required outputs

Produce all of the following:

1. A clear workspace structure.
2. Raw transcript staging.
3. Normalized transcript files.
4. Chunked artifacts with stable ids.
5. Topic and entity indexes.
6. Wiki pages for episodes, themes, people, and concepts.
7. An Obsidian export folder.
8. A QA report describing what worked, what failed, and what was skipped.
9. A concise run report with next-step recommendations.

## Workflow

### Step 1: Inspect the corpus

- Discover all available transcript sources.
- Identify file formats, naming conventions, and metadata availability.
- Detect missing or duplicate items.

### Step 2: Stage raw data

- Copy raw files into a dedicated inbox.
- Never overwrite originals.
- Track source paths and checksums if possible.

### Step 3: Normalize transcripts

- Clean text.
- Preserve useful speaker and episode metadata.
- Standardize formatting.
- Keep traceability back to the source.

### Step 4: Chunk intelligently

- Chunk by semantic boundaries, not arbitrary length alone.
- Attach metadata to every chunk.
- Maintain overlap where helpful for retrieval.

### Step 5: Build indexes

- episode index
- speaker index
- topic index
- concept index
- quote index
- cross-reference index

### Step 6: Generate wiki pages

For each page, include:

- title
- summary
- key points
- related pages
- source references

Prefer high-signal pages over noisy exhaustive ones.

### Step 7: Export to Obsidian

- Emit markdown files with stable names.
- Use internal wiki links.
- Keep frontmatter clean and consistent.
- Ensure the export is easy to open as an Obsidian vault.

### Step 8: Validate

- check for broken links
- check for empty pages
- check for duplicate content
- verify that the export folder is complete

### Step 9: Report

Return a final report that includes:

- what was built
- what was skipped
- blockers
- confidence level
- recommended next action

## Quality bar

The output should look like a strong internal research wiki:

- organized
- navigable
- useful for future retrieval
- resilient enough to rerun

## If something blocks you

Do this in order:

1. Log the blocker clearly.
2. Use the best available fallback.
3. Continue processing other items.
4. Explain the residual gap in the final report.
