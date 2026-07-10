# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

## Related

- [Agent workspace](/concepts/agent-workspace)

## Backup

- Layer 1 backup: `sfs-mission-control` is backed up to Bitbucket repo `https://bitbucket.org/Bresleveloper/wiki-kb.git`.
- Bitbucket username: `Bresleveloper`
- Token storage: workspace root `.env` as `BITBUCKET_ARIEL_WIKIKB`
- Repository access token fallback: `sfs-mission-control/bitbucket.env` contains the Bitbucket repo access token instructions for `wiki-kb`; Git works with the documented `x-token-auth` URL form.
- Runtime artifacts are intentionally excluded from the backup repo via `sfs-mission-control/.gitignore`.

## Mission Control

### Mission Control JSON Answer Shape

When Mission Control calls Snoracle through OpenClaw, the API reminder is: "return Mission Control JSON only as described in TOOLS.md".

Return JSON only, with this top-level shape:

```json
{
  "question_id": "q_...",
  "status": "done",
  "summary_answer_markdown": "...",
  "boxes": {
    "wikillm": {"selected": true, "status": "used|not_selected|no_useful_evidence|failed", "answer_markdown": "...", "citations": [], "evidence": [], "errors": []},
    "obsidian": {"selected": true, "status": "used|not_selected|no_useful_evidence|failed", "answer_markdown": "", "citations": [], "evidence": [], "errors": []},
    "raw": {"selected": true, "status": "used|not_selected|no_useful_evidence|failed", "answer_markdown": "...", "citations": [], "evidence": [], "errors": []}
  },
  "disagreements": [],
  "sources_used_footer": "Sources Used: ... | Evidence items: ...",
  "labels": ["Corpus", "Raw", "Snoracle thinks"],
  "candidate": false
}
```

Rules:

- Answer in Hebrew unless David explicitly asks otherwise.
- Every paragraph must have a source label or citation label.
- Preserve the three source boxes even when a source is not selected.
- Obsidian does not exist yet. If accidentally called, return an empty string and no evidence.
- If the answer is meaningful enough to become future knowledge, set candidate to true. Mission Control will store that as candidate = 1 and digested = 0.
- Do not claim wiki updates were applied. Mission Control only marks candidates for future digestion.

### Mission Control Query Responsibility

Snoracle is responsible for reasoning before querying sources.

For each Mission Control question:

1. Understand the user question as a research task, not just as keywords.
2. Decide what each selected source must prove, disprove, or clarify.
3. Create meaningful source-specific queries for WikiLLM, Obsidian, and raw transcripts.
4. Use Hebrew and English variants when relevant.
5. Use OpenClaw sessions/subagents/tools as appropriate for each selected source.
6. Wait for source results before writing the final synthesis.
7. Put source-specific findings in their own boxes, then write the cross-source summary above them.
8. Label outside knowledge explicitly if used.

Mission Control should create and store a dedicated OpenClaw session per question so runs can be tracked, cancelled, inspected, and audited later.
