# TOOLS.md - Research Categorization Agent Local Notes

## Mandatory Files

Before every research task, reread:

- [Categorization Agent Mission Statement.md](/root/.openclaw/workspace-research-categorization/Categorization%20Agent%20Mission%20Statement.md)

For global system context, reference:

- [System High Level Goals.md](/root/.openclaw/workspace-research-categorization/System%20High%20Level%20Goals.md)

## Research Workflow

Use browser/web evidence rather than internal model memory for company categorization.

Default verification sequence:

1. Company name + product/technology/sub-sector searches.
2. Company website, especially product, technology, clinical, regulatory, publications, and news pages.
3. Start-Up Nation Finder and IATI sources when accessible.
4. PubMed or ClinicalTrials.gov for clinical and therapeutic claims.
5. FDA, CE/MDR, or other regulatory sources when classification depends on device/software/drug status.

## Classification Tools And Evidence Targets

Primary evidence to seek:

- product mechanism of action,
- proprietary hardware vs. software dominance,
- biological/chemical therapeutic mechanism,
- target clinical condition,
- regulatory class/status,
- clinical validation,
- source URLs and confidence level.

## Output Standards

- Use the authorized taxonomy from the mission file.
- Do not invent categories.
- Mark unknown fields as N/A.
- Preserve source traceability.
- Explain ambiguity when classification is not straightforward.
- Prefer structured Markdown that can be ingested into a graph workflow.

## Research Output Folders

Use [research/](/root/.openclaw/workspace-research-categorization/research/) as the root folder for research deliverables.

- [research/entities/](/root/.openclaw/workspace-research-categorization/research/entities/) - one company/entity categorization file per entity.
- [research/batches/](/root/.openclaw/workspace-research-categorization/research/batches/) - multi-company or task-level batch outputs.
- [research/sources/](/root/.openclaw/workspace-research-categorization/research/sources/) - source notes, captured references, and evidence logs when useful.
- [research/templates/](/root/.openclaw/workspace-research-categorization/research/templates/) - reusable Markdown schemas and output templates.

Default behavior: save completed research outputs into the relevant subfolder unless David asks for a different location.

## Feedback Lessons

When David gives feedback after any task, create a new file under [lessions/](/root/.openclaw/workspace-research-categorization/lessions/).

Suggested filename:

`YYYY-MM-DD-short-topic.md`

Required sections:

```markdown
# Lesson: [topic]

## Task

## Delivered Result

## David's Feedback

## Gap Analysis

## Root Cause

## Fix

## Future Checklist
```
