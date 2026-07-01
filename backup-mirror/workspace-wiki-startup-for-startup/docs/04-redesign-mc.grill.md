# Mission Control Redesign Grill

These are the remaining questions after rebuilding docs/04-redesign-mc.md from David's responses.

## Open Questions

1. Fresh session syntax:
Should the v1 API call OpenClaw with openclaw agent --agent <snoracle-agent-id> and no --session-id to force a fresh full agent turn, or should it create/store an explicit session id per question if the CLI exposes one?

2. Agent id:
Which agent id should Mission Control target in production: the current wiki-startup-for-startup Snoracle agent, or a separate mission-control-specific agent id with the same workspace context?

3. JSON schema location:
Is TOOLS.md enough as the schema source for the test, or should the API also pass a short inline reminder that says "return Mission Control JSON only" on every CLI call?

4. Raw OpenClaw output handling:
If OpenClaw returns non-JSON text around the JSON, should the API extract the first valid JSON object and store the full raw output separately, or should any non-JSON wrapper mark the run failed?

5. Cancel behavior:
Is v1 cancellation allowed to kill only the local OpenClaw subprocess and mark the question cancelled, while OpenClaw-level session/task cancellation remains TBD?

6. Candidate flag authority:
Should candidate = 1 be controlled only by Snoracle's returned JSON, or can the human UI also toggle candidate after reviewing an answer?

7. Digestion workflow:
Should digested = 1 mean "already turned into WikiLLM/Obsidian knowledge", or more narrowly "reviewed and no further action needed"?

8. Source box defaults:
Until Obsidian exists, should the UI still show Obsidian checked by default, or should it stay unchecked while preserving the empty source box?

9. Gate URL handling:
Should docs avoid writing the literal gate parameter at all, or is it acceptable in private implementation docs as long as it never appears in HTML/JS?

10. Timeout value:
What timeout should v1 use for an OpenClaw agent turn: 5, 10, 15, or 20 minutes? Current code used long timeouts; latency is acceptable, but the API still needs a hard bound.

## Resolved By David

- Self-signed certificate is correct for this stage.
- Port 40006 should be HTTPS-only.
- HTTP on 40006 should not serve the app.
- Static gate remains required, but must not be exposed in HTML/JS.
- Keyword-only retrieval is not the product direction.
- Source querying and citation responsibility belong to Snoracle/subagents.
- Detailed progress events, SSE optimization, evidence pagination, restart resumption, and broad integration-test expansion are not active redesign items right now.
- Auto wiki patch workflow is out of scope for now; use candidate/digested flags instead.

