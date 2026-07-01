# Customer Requirement Spec

## Working Title

Wiki LLM Agent for Podcast and Multi-Source Knowledge Bases

## Problem Statement

The customer wants an agentic system that can ingest raw materials, turn them into a structured knowledge base, connect related concepts, detect contradictions, answer questions, and continuously improve from feedback.

The first MVP should focus on the Startup for Startup podcast by Monday.com, a large Hebrew podcast corpus with more than 350 episodes and substantial strategic, product, and ecosystem knowledge.

The longer-term vision is a reusable framework that can be applied to other knowledge bases, especially meeting archives for organizations.

## Product Goals

1. Ingest raw source material from convenient channels, ideally WhatsApp on a phone.
2. Convert episodes or documents into a durable wiki-style knowledge base.
3. Link related concepts, episodes, topics, and evidence.
4. Answer questions over the corpus in a conversational way.
5. Detect contradictory or suspicious inputs and ask for confirmation when needed.
6. Support iterative feedback and reprocessing so the knowledge base improves over time.
7. Export cleanly to Obsidian with a graph-friendly structure.
8. Run securely on a VPS/cloud deployment with backup and recovery.

## Core Use Cases

### MVP 1: Podcast Knowledge Base

- User sends podcast files, links, or transcripts.
- System ingests Monday.com Startup for Startup podcast episodes.
- System extracts:
  - episode summaries
  - key topics
  - named entities
  - themes
  - cross-episode links
  - contradictions or unresolved claims
- System answers questions like:
  - What did they say about Agent Labs?
  - Which episodes discuss change management?
  - What are the recurring beliefs about SaaS and AI?
- System exposes the result in Obsidian and through a chat interface.

### MVP 2: Organization Meeting Knowledge Base

- Same framework, different corpus.
- Ingests meeting recordings, transcripts, or written notes.
- Builds a searchable team memory / organizational wiki.
- Must be easy to clone and onboard for a new organization or topic.

## User Experience Requirements

- Input should be as low-friction as possible.
- WhatsApp is the preferred intake channel.
- The system should also support other channels if they are easier or more reliable.
- The user should be able to:
  - ask questions
  - provide feedback on errors
  - request reprocessing
  - review the knowledge base visually in Obsidian
- The system should feel like a helpful expert, not a generic chatbot.

## Functional Requirements

### Ingestion

- Accept files, transcripts, and links.
- Support automatic monitoring for new podcast episodes.
- Pull from reliable sources such as YouTube and other accessible platforms.
- Preserve source metadata and provenance for every ingested item.

### Normalization

- Convert raw inputs into a normalized internal format.
- Keep every word and source detail available at the transcript layer.
- Separate raw transcript, cleaned transcript, and synthesized summaries.

### Knowledge Construction

- Create wiki pages per episode, topic, concept, and relevant entity.
- Link related pages bidirectionally.
- Store evidence references so claims can be traced back to sources.
- Build a graph of concepts and relationships.

### Question Answering

- Provide answers over the knowledge base.
- Prefer evidence-backed responses.
- Reference source episodes or passages when possible.
- Support correction and feedback after answers.

### Contradiction Handling

- Detect when new inputs conflict with existing knowledge.
- Ask the user for confirmation when the system is not confident.
- Support a circuit-breaker flow for obviously unrelated or suspicious content:
  - confirm whether to correct the current knowledge base
  - ask whether to create a new knowledge base instead

### Continuous Improvement

- Incorporate user feedback into future runs.
- Reprocess affected pages or indexes after corrections.
- Maintain a stable source-of-truth pipeline so knowledge can be refreshed safely.

### Obsidian Export

- Export a clean Obsidian vault.
- Support graph navigation and linked pages.
- Make the exported structure readable on desktop and phone.

### Backup and Safety

- Back up the knowledge base and index artifacts.
- Avoid losing a working corpus.
- Support restore/rebuild from source data.

## Architecture Requirements

- Run on a VPS or cloud-hosted environment.
- Be modular enough to support multiple knowledge bases.
- Keep knowledge-base configuration separate from the ingestion engine.
- Use a reusable pipeline that can be pointed at different corpora.

## Data Model Requirements

Each source item should keep:

- source type
- source URL or path
- ingestion timestamp
- raw text or transcript
- normalized text
- summary
- topics
- entities
- links
- confidence and quality signals
- feedback history

## Non-Functional Requirements

- Accuracy over flashy automation.
- High traceability from answer to source.
- Easy maintenance.
- Fast enough for daily use.
- Secure by default.
- Backup-aware.
- Simple to duplicate for new corpora.

## MVP Success Criteria

MVP 1 is successful if:

- the user can send a podcast episode
- the system ingests it without manual cleanup
- the system builds useful wiki pages and links
- the system can answer topical questions reliably
- the user can correct mistakes and see the corpus improve
- the result exports cleanly to Obsidian

## Open Questions

1. Should WhatsApp be the only intake channel, or just the preferred one?
2. Do you want the first corpus to include only Startup for Startup, or also show how the system would be adapted for meetings?
3. Should answers be optimized for Hebrew, English, or both?
4. Do you want automatic episode discovery to poll YouTube only, or also other sources?
5. Should the system generate formal summaries, or preserve a more source-faithful wiki style?
6. How strict should contradiction detection be before asking for confirmation?

## Recommendation

Start with MVP 1 focused narrowly on Startup for Startup, but design the pipeline as if it will later be cloned for other corpora. That gives you a practical first product without locking the architecture to podcasts only.

## Proposed Architecture

The system should be split into small modules so the same engine can support different corpora later.

### 1. Intake Layer

- Accept WhatsApp audio, uploaded files, transcripts, and links.
- Store every original asset immutably.
- Attach source metadata, timestamps, and corpus tags.

### 2. Transcription and Normalization Layer

- Convert raw audio into text.
- Normalize formatting without losing source fidelity.
- Preserve raw transcript, cleaned transcript, and derived summaries separately.

### 3. Knowledge Builder

- Turn the normalized corpus into wiki pages, entities, topics, and linked concepts.
- Build cross references between episodes and themes.
- Detect contradictions and mark unresolved claims.

### 4. Answering Layer

- Provide conversational search and grounded answers.
- Cite the source episodes or passages used for each answer.
- Let the user rate or correct the answer.

### 5. Feedback and Reprocessing Layer

- Capture user corrections.
- Rebuild affected pages and indexes from the corrected source.
- Keep prior versions available for audit and rollback.

### 6. Export and Presentation Layer

- Export to Obsidian.
- Support a readable graph and a clean page hierarchy.
- Keep the exported structure consistent across corpora.

### 7. Ops Layer

- Backups
- Restore path
- Run logs
- Observability for ingestion and rebuild jobs

## User Flows

### Flow 1: New Customer Story

1. Customer sends a voice recording.
2. System transcribes the audio.
3. System extracts needs, constraints, and success criteria.
4. System drafts a requirement document.
5. System asks follow-up questions only if there is a blocking ambiguity.
6. System writes the final package into the project folder.

### Flow 2: Revision Loop

1. Customer reviews the draft.
2. Customer corrects or clarifies a point.
3. System updates the spec and keeps the previous draft in the archive.
4. System records the run in the audit log.

### Flow 3: New Corpus Onboarding

1. Copy the pipeline template.
2. Point it at a new corpus.
3. Reuse the same intake, normalization, linking, answer, and export steps.
4. Keep the corpus-specific config isolated from the core engine.

## Acceptance Criteria

The work is acceptable when all of the following are true:

- The requirement doc clearly describes MVP 1 and MVP 2.
- The architecture section explains how the system is modular and reusable.
- The user-flow section makes the operational process unambiguous.
- The file-management rules are explicit and durable.
- The spec includes a clear acceptance definition for the developer.
- The project contains raw input, transcript, final spec, open questions, and run log artifacts.

## Delivery Phases

### Phase 1

- Intake raw audio and produce transcripts.
- Draft the requirement spec.
- Capture open questions.

### Phase 2

- Add architecture and user flows.
- Add acceptance criteria and non-functional requirements.
- Refine the file-management contract.

### Phase 3

- Use the project repeatedly for future customer stories.
- Keep improving the template and log format from real usage.

## Project Operating Rule

Every future customer story should be processed as a repeatable run:

1. Ingest raw material.
2. Store transcript and evidence.
3. Draft the requirement spec.
4. Add open questions only if needed.
5. Save the final artifact.
6. Record the run.
7. Archive superseded versions instead of deleting them.
