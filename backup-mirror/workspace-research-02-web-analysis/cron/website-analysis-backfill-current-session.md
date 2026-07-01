# website-analysis-backfill-current-session

This is a local review copy of the saved OpenClaw cron job.
The actual runnable job is stored in the OpenClaw scheduler, not as a `systemd` unit or workspace cron file.

## Live Job Identity

- Job ID: `c5b456bd-cae7-4b35-85d2-754ce2ebea33`
- Agent ID: `research-02-web-analysis`
- Session Key: `agent:research-02-web-analysis:main`
- Name: `website-analysis-backfill-current-session`
- Enabled: `true`

## Schedule

- Kind: `every`
- Every: `10800000` ms
- Interval: 3 hours
- Anchor: `1780474913454`
- Wake Mode: `now`

## Session Binding

- Session Target: `session:agent:research-02-web-analysis:main`
- Payload Kind: `agentTurn`
- Delivery Mode: `none`
- Thinking: `high`
- Timeout Seconds: `3600`
- Light Context: `true`

## Payload Message

```text
You are running from the current-session cron backfill job for the Website Analysis Agent.

Follow this procedure exactly:
1. Reread `/root/.openclaw/workspace-research-02-web-analysis/Website Analysis Agent Mission Statement.md` before doing any research.
2. List file basenames in `/root/.openclaw/workspace-research-categorization/research/entities` and `/root/.openclaw/workspace-research-02-web-analysis/research/entities`.
3. Ignore non-entity placeholders such as `.gitkeep`.
4. Compute the set difference: files present in the categorization folder and missing from the website-analysis folder.
5. If there are no missing files, remove the cron job named `website-analysis-backfill-current-session` with the cron tool, then stop.
6. If there are missing files, choose exactly one file only. Use deterministic selection: lexicographically first missing filename.
7. Use that selected entity file as the target company for research.
8. Read the selected categorization file for context.
9. Perform website-analysis research for that company according to the mission statement. Use browser/web/search evidence, not recalled facts.
10. Produce a complete deliverable in `/root/.openclaw/workspace-research-02-web-analysis/research/entities/<same filename>`.
11. Use the Website Analysis Agent markdown schema from the mission statement. Keep all sections. Use `N/A` where evidence is unavailable.
12. Write the file to disk.
13. Keep the run scoped to one company only, then stop.

Quality bar:
- Prefer official company pages plus independent institutional verification when available.
- Distinguish pilot signals from commercial-contract signals using external confirmation, scope language, and hard metrics where possible.
- Capture marketing gaps and implied engineering needs explicitly.
- Do not delete headers to make the output look cleaner.
```
