# Mission Control Redesign Plan

This is the active implementation plan after David's grill answers.

The core correction is simple: Mission Control is an API shell around the real Snoracle agent. The backend should persist the question, call OpenClaw for a full Snoracle agent turn, capture whatever comes back, store it, and show it in the web UI. Snoracle and its subagents own source-query reasoning.

## Decision Summary

- Architecture: API -> OpenClaw CLI full Snoracle turn -> API -> frontend.
- Target agent: always the current `wiki-startup-for-startup` Snoracle agent. Do not create a separate Mission Control agent.
- Session model: create and store a dedicated OpenClaw session per Mission Control question so the app can track, cancel, inspect, and later resume/audit runs.
- Prompt model: the API passes a short action prompt plus the inline reminder: "return Mission Control JSON only as described in TOOLS.md".
- Output handling: the API returns whatever the agent returns. It may parse JSON opportunistically for storage/UI fields, but non-JSON output is not a request failure during this phase.
- Timeout: start with 5 minutes per OpenClaw agent turn.
- Source reasoning: no keyword-only backend retrieval as the product path. Snoracle/subagents reason about the question and create source-specific queries.
- Candidate workflow: store `candidate` and `digested` bit columns. No automatic wiki patch workflow now.
- Gate: `40006` checks the server-side gate. If the request is not gated or already authenticated from a gate exchange, drop/ignore it. Do not expose the gate value in HTML or browser JS.
- Transport: `40006` is HTTPS-only with the current self-signed certificate approach.
- Progress UI: loader on when query starts; loader off when response/error returns.

## Implementation Status - 2026-07-01

- Implemented the full OpenClaw/Snoracle turn bridge in `sfs-mission-control/mission_control/snoracle_adapter.py`.
- Verified the command path with a real CLI probe: `openclaw agent --agent wiki-startup-for-startup --session-id <id> --message ... --timeout 15 --json` completed and returned a top-level `runId`.
- Stored explicit-session keys in OpenClaw's observed format: `agent:wiki-startup-for-startup:explicit:<session-id>`.
- Added question-row metadata for OpenClaw session/run ids, subprocess pid/timing, stdout/stderr/raw output paths, raw response text, parse status, `candidate`, and `digested`.
- Removed the local keyword worker path from the primary answer flow. The old workers remain only as development utilities/tests.
- Disabled automatic wiki patch creation. This phase stores only `candidate` and `digested`.
- Enforced HTTPS-only startup and hidden server-side gate behavior.
- Simplified the frontend to loader/polling plus raw/parsed answer display.
- Implemented layered cancellation: browser polling abort, backend status cancellation, local subprocess group kill, then best-effort `openclaw tasks cancel <lookup>` using task id, run id, or explicit session key.

## Plan 01 - Full OpenClaw/Snoracle Turn

Simple explanation:
Mission Control should call Snoracle as a real OpenClaw agent turn. The backend should not attempt to replace Snoracle with local synthesis or keyword workers.

Source reason:
David wants the OpenClaw agent path because Snoracle has the tuned workspace files, system prompt, TOOLS.md guidance, and tool/subagent access. The OpenClaw docs confirm `openclaw agent` is the CLI path for a full agent turn and supports `--agent`, `--session-id`, `--message`, `--thinking`, `--timeout`, and `--json`.

Fix suggest:
Rewrite the adapter into an api-cli-api bridge:

1. Public API receives question and selected source boxes.
2. API creates a SQLite question row.
3. API generates a Mission Control OpenClaw session id/key for that question and stores it.
4. API builds a short prompt containing question id, source selections, user question, and the reminder: "return Mission Control JSON only as described in TOOLS.md".
5. API calls the current Snoracle agent through OpenClaw with a 300 second timeout.
6. Snoracle reasons about the question, uses subagents/tools for selected source types, and returns the answer.
7. API stores stdout, stderr, exit code, timings, session metadata, and parsed JSON if parsing succeeds.
8. API returns the raw/full agent output to the frontend for review.

Initial command shape to verify in implementation:

```bash
openclaw agent \
  --agent wiki-startup-for-startup \
  --session-id <mission-control-session-id> \
  --message "<action prompt>" \
  --thinking xhigh \
  --timeout 300 \
  --json
```

If the CLI rejects combining `--agent` and `--session-id`, use the Gateway/session API path documented in OpenClaw protocol: create/resolve a session for `wiki-startup-for-startup`, then send to that session. Do not silently fall back to the visible human chat route.

Why this solves it:
The intelligence layer becomes the actual Snoracle agent while the API remains a reliable persistence and delivery layer.

## Plan 02 - Store OpenClaw Session/Run Metadata

Simple explanation:
Each Mission Control question needs its own tracked OpenClaw execution identity.

Source reason:
David answered that Mission Control should create and store sessions because it lets us control sessions now and is useful later. OpenClaw docs say a session key points to a current session id, and `--session-id` reuses an explicit session.

Fix suggest:
Add fields to the question table or a related `agent_runs` table:

- `openclaw_agent_id`
- `openclaw_session_id`
- `openclaw_session_key`
- `openclaw_run_id`
- `openclaw_task_id`
- `cli_pid`
- `cli_started_at`
- `cli_finished_at`
- `cli_exit_code`
- `cli_stdout_path`
- `cli_stderr_path`
- `raw_response_path`

Use deterministic ids where possible, for example session ids derived from the question id plus a random suffix. Store raw command output under `sfs-mission-control/mission_control/logs/runs/<question_id>/`.

Why this solves it:
Cancellation, debugging, audit, and future session reuse become concrete instead of relying on an anonymous subprocess.

## Plan 03 - Mission Control Contract In TOOLS.md

Simple explanation:
The JSON answer shape and source-query responsibilities belong in TOOLS.md so Snoracle sees them as part of its local operating context.

Source reason:
David explicitly asked to put the structured response schema in TOOLS.md for testing and to pass only a short reminder in the API prompt.

Fix suggest:
Keep the Mission Control JSON schema and source-query instructions in TOOLS.md. The API prompt should not repeat the full schema; it should say: "return Mission Control JSON only as described in TOOLS.md".

Why this solves it:
The prompt stays short while Snoracle still has the full contract in workspace context.

## Plan 04 - Source Querying Is Snoracle's Job

Simple explanation:
Mission Control should not hardcode naive retrieval as its core product behavior. Snoracle should understand the question and decide how to query WikiLLM, Obsidian, and raw transcripts.

Source reason:
David rejected keyword-only retrieval because the whole point of GPT plus OpenClaw is to let the AI agent/subagents reason about the question before querying sources.

Fix suggest:
Move source work into Snoracle instructions:

1. Understand the question as a research task.
2. Decide what each selected source needs to prove, disprove, or clarify.
3. Create source-specific queries, including Hebrew/English variants when useful.
4. Use subagents/tools for selected data-source types.
5. Wait for source results.
6. Preserve the three source boxes in the final answer.

Backend local workers may remain temporarily as fallback/dev utilities, but they are not the primary answer path.

Why this solves it:
The source retrieval layer becomes adaptive and research-aware instead of token matching.

## Plan 05 - Raw Output Is Always Returned

Simple explanation:
For this phase, the app should not fail just because Snoracle returns extra text or imperfect JSON.

Source reason:
David answered that no matter what the agent returns, the API should return it so he can read and decide himself.

Fix suggest:
Store and return raw output always. If JSON parsing succeeds, use it to populate structured UI fields. If parsing fails, show raw output in the answer area and mark the structured parse status as failed internally.

Why this solves it:
Testing can continue even when the agent contract is imperfect. Bad output becomes visible product feedback, not a backend blocker.

## Plan 06 - Five Minute Timeout And No Stuck API

Simple explanation:
The API must have a hard bound around OpenClaw calls.

Source reason:
David chose 5 minutes after observing that the first test question was fast. Current code used much longer timeouts.

Fix suggest:
Set the OpenClaw CLI timeout to 300 seconds. Around the CLI call, write pre/post logs:

- before: question id, session id, selected sources, command shape without secrets, timestamp
- after success: duration, exit code, stdout path, stderr path, parsed JSON status
- after failure/timeout: duration, error class, stdout/stderr paths, cancellation state

Why this solves it:
The web request lifecycle is bounded and every run has a trace.

## Plan 07 - Cancel Must Kill The Agent Session/Run

Simple explanation:
Cancellation is not just a UI state. It must cancel frontend waiting, backend subprocess work, and the active OpenClaw agent session/run as far as OpenClaw supports it.

Source reason:
David clarified that cancel should kill the agent session and cancel the API request on frontend and backend. OpenClaw docs show several relevant mechanisms but the exact foreground-agent cancellation path still needs implementation verification:
- Agent loop docs mention AbortSignal/cancel and timeout as early end paths.
- Gateway protocol exposes `tasks.cancel`.
- `openclaw tasks cancel <lookup>` accepts a task id, run id, or session key for background tasks.
- FAQ stop triggers exist as standalone messages, but that is not a proven API-level foreground cancellation path.

Fix suggest:
Implement cancellation in layers:

1. Frontend aborts the active fetch/poll and marks the UI cancelled.
2. Backend marks the question cancelling/cancelled.
3. Backend kills the local OpenClaw subprocess process group.
4. Backend uses stored `openclaw_task_id`, `openclaw_run_id`, or `openclaw_session_key` to call the strongest available OpenClaw cancellation path, starting with `openclaw tasks cancel <lookup>` when a task/run record exists.
5. If no cancellable task is discoverable, record that OpenClaw-level cancellation was unavailable and keep the local subprocess kill as the hard stop for the API request.

Acceptance note:
A UI-only cancel is not acceptable. The implementation must prove, in logs, what was killed locally and what OpenClaw cancellation path was attempted.

Why this solves it:
The API and browser stop immediately, and the app has a concrete audit trail for whether the underlying OpenClaw run also stopped.

## Plan 08 - HTTPS-Only Public App

Simple explanation:
Port 40006 should serve HTTPS only.

Source reason:
David said HTTPS only always for 40006 and self-signed certificate is the correct solution for this stage.

Fix suggest:
Require TLS certificate/key at startup for 40006. If missing, fail startup. Remove HTTP origins from allowed origins. Do not serve the app over HTTP.

Why this solves it:
There is one deployment mode and no accidental plaintext app.

## Plan 09 - Gate Handling

Simple explanation:
The server should enforce the v1 gate itself and should not advertise the gate in the UI.

Source reason:
David clarified that `server.py` for 40006 should check whether the gate exists; if not, ignore/drop the request. He also said the gate value should not appear anywhere in HTML/JS.

Fix suggest:
Keep the gate check server-side:

- No visible login link.
- No gate value in static HTML/JS.
- Requests without valid gate entry or previously established gate auth get a minimal no-content/404 style response.
- If keeping the current cookie exchange, the exchange must be internal and invisible: valid gate -> cookie -> redirect/root; no gate and no cookie -> drop/ignore.

Why this solves it:
The app remains gated without publishing the gate value to browser code or unauthenticated visitors.

## Plan 10 - Candidate And Digested Flags Only

Simple explanation:
Mission Control should not auto-patch the wiki in this phase.

Source reason:
David wants only candidate/digested bits for now. `digested = 1` means the answer was already turned into WikiLLM/Obsidian knowledge, but the digestion workflow itself does not matter now. Candidate flag authority is still TBD, so use the minimal default.

Fix suggest:
Add these columns:

- `candidate INTEGER NOT NULL DEFAULT 0`
- `digested INTEGER NOT NULL DEFAULT 0`

For this phase:

- Snoracle can set `candidate: true` in returned JSON.
- The API stores that as `candidate = 1`.
- `digested` remains `0` until a later workflow.
- Disable/bypass automatic wiki patch job creation.
- Do not implement a human candidate toggle yet unless it becomes necessary.

Why this solves it:
Useful answers are preserved for future knowledge digestion without pretending the patch workflow exists.

## Plan 11 - Simple Loader Only

Simple explanation:
Detailed progress events are out of scope for this phase.

Source reason:
David asked to remove progress-event work for now and just use a loader.

Fix suggest:
Show loader when a query starts. Remove loader when the CLI/API result returns or fails. Keep detailed runtime diagnostics in log files, not the UI.

Why this solves it:
The frontend stays simple while the backend architecture is corrected.

## Plan 12 - Obsidian Placeholder

Simple explanation:
Obsidian does not exist yet and should not add noisy placeholder text.

Source reason:
David said accidental Obsidian calls should currently return an empty string.

Fix suggest:
Until the vault exists, Obsidian source output should be empty: empty answer string, empty evidence list, and no noisy "no Obsidian yet" copy.

Why this solves it:
The three-box shape can remain without polluting every answer.

## Immediate Build Order

1. Update adapter to generate/store per-question OpenClaw session/run metadata.
2. Call `openclaw agent` against `wiki-startup-for-startup` with the stored session id, 300 second timeout, xhigh thinking, JSON mode, and the TOOLS.md reminder.
3. Store stdout/stderr/raw response and return raw output to the frontend regardless of JSON parse success.
4. Remove local source workers from the primary answer path and rely on Snoracle/subagents for source querying.
5. Add `candidate` and `digested` columns; stop automatic wiki patch jobs.
6. Enforce HTTPS-only startup and HTTPS-only origins.
7. Remove visible gate link/value from HTML/JS; drop unauthenticated ungated requests.
8. Simplify UI progress to loader-on/loader-off.
9. Implement cancellation layers and log what was actually stopped.

## Evidence Checked

- `openclaw agent` docs: supports `--agent`, `--session-id`, `--message`, `--thinking`, `--timeout`, and `--json`.
- Agent send docs: `--agent <id>` targets a configured agent; `--session-id <id>` reuses an existing session.
- Session management docs: each session key points at a current session id; session id is the transcript id.
- Agent loop docs: OpenClaw runs are serialized per session and can end early by timeout, AbortSignal/cancel, Gateway disconnect, or RPC timeout.
- CLI probe: `openclaw agent --agent wiki-startup-for-startup --session-id <id> --message ... --timeout 15 --json` accepts the selector combination and returns a top-level `runId`.
- Tasks docs/help: `openclaw tasks cancel <lookup>` can cancel background tasks by task id, run id, or session key. Foreground CLI cancellation through this path is still best-effort, so Mission Control first kills the local subprocess group and logs the OpenClaw cancellation attempt result.
- Current code proof: existing adapter passes full prompt via `--message` and has local prompt compaction constants; this should be replaced by a short action prompt.
