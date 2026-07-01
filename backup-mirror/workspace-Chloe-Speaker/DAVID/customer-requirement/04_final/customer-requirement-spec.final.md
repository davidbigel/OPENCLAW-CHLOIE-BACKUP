# Customer Requirement Spec - Final

This is the developer-facing final version for the current intake cycle.

Source project: customer-requirement

Primary goal:
- Build a reusable wiki/LLM knowledge-base agent that can ingest raw sources, organize them into a graph of wiki pages, answer questions, detect contradictions, and improve from feedback.

First MVP:
- Start with the Startup for Startup podcast corpus from Monday.com.

Secondary MVP:
- Reuse the same pipeline for organizational meeting knowledge bases.

Operating contract:
- Keep raw inputs immutable.
- Keep transcripts and analysis separate.
- Save final outputs here.
- Preserve run logs and archive superseded versions instead of deleting them.
