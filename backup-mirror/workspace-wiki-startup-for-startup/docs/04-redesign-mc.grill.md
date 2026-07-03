# Mission Control Redesign Grill

No open user questions for this phase.

## Implementation Research Notes

- Verified command path on 2026-07-01:
  `openclaw agent --agent wiki-startup-for-startup --session-id <id> --message ... --thinking low --timeout 15 --json` completed successfully.
- The successful CLI probe returned a top-level `runId`, so Mission Control now extracts and stores `runId/run_id` when present.
- For explicit sessions, OpenClaw reports the session key shape as `agent:wiki-startup-for-startup:explicit:<session-id>`. Mission Control now stores that key instead of inventing a separate label.
- `openclaw tasks cancel <lookup>` accepts task id, run id, or session key. This is implemented as the best available OpenClaw-level cancellation attempt after killing the local subprocess group.
- A foreground `openclaw agent` run has not been proven to be fully cancellable through `tasks cancel` in every case. The guaranteed stop for Mission Control is the local subprocess group kill; OpenClaw cancellation attempts are logged with their result.

## Phase Scope Boundary

No Obsidian build, wiki digestion workflow, human candidate toggle, or progress-event UI is in scope for this phase.

