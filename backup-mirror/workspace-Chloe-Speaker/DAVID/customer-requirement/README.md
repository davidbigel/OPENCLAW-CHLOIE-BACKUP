# Customer Requirement Project

Use this project to turn raw customer voice notes into implementation-ready requirement documents.

## Workflow

1. Customer sends a voice recording with needs, goals, constraints, and context.
2. I transcribe and extract the requirements.
3. I ask follow-up questions only when a gap blocks a solid spec.
4. I write a polished requirement document for the developer.
5. I save all outputs in this project folder for traceability.

## Structure

- 00_raw/ - original recordings or source notes
- 01_transcripts/ - transcription outputs
- 02_requirements/ - drafted requirement docs
- 03_questions/ - follow-up questions if needed
- 04_final/ - final developer-ready specs
- 05_runs/ - run logs, timestamps, and processing notes
- 99_archive/ - deprecated drafts or superseded outputs

## Intake Rule

Treat every voice note as raw customer input. Do not assume the customer is describing the full solution; extract intent, constraints, edge cases, and success criteria.

## File Management Rules

- Never overwrite raw inputs.
- Every intake gets a dated filename.
- If a document changes materially, write a new version rather than editing in place.
- Keep the final spec in `04_final/` and all supporting evidence in the earlier folders.
- Record each completed processing run in `05_runs/` so the project has a durable audit trail.
- Move superseded artifacts to `99_archive/` instead of deleting them when cleanup is needed.
