# Mission Control Redesign Plan

This is the corrected plan after David reviewed the first redesign draft.

The old audit-style list was too broad. The active plan is now narrower: Mission Control should stop doing local source-worker synthesis and instead ask the real Snoracle agent, through OpenClaw, to run a full agent turn with the workspace system prompts, TOOLS.md guidance, and source-specific subagents/tools.

## Decision Summary

- Use OpenClaw/Snoracle as the intelligence layer, not keyword-only backend retrieval.
- The backend API should persist the question, call OpenClaw CLI/API, capture the full answer, store it, and dump it to the frontend for human review.
- Latency is acceptable for now if it buys better reasoning and uses Snoracle's full prompt/memory/tool context.
- Fresh one-shot agent turns are the current target. Persistent Mission Control sessions are a future option and should be documented in code/spec comments only.
- Port 40006 is HTTPS-only. HTTP should not serve the app.
- The public gate remains a server-side guardrail, but the literal gate URL must not appear in HTML or browser JS.
- Self-signed TLS is correct for this stage.
- The wiki-patch workflow is out of scope for now. Store candidate/digested flags in SQLite and do no automatic patch action.
- UI progress can be simple for now: show loader when a query starts, remove loader when the CLI/API result returns.

## Plan 01 - Replace Backend Synthesis With A Full OpenClaw Agent Turn

Simple explanation:
Mission Control should not synthesize with local keyword workers. It should ask Snoracle to handle the question as an OpenClaw agent turn, because Snoracle has the tuned workspace files, system prompt, and session/tool behavior that the API layer lacks.

Source reason:
The current adapter builds a local fallback and then tries to call OpenClaw from mission_control/snoracle_adapter.py. The CLI help confirms the available command shape: openclaw agent supports --agent, --session-id, --message, --thinking, --timeout, and --json. David's input is that an OpenClaw agent call returns a full answer and should be the primary path.

Fix suggest:
Rewrite the adapter into an api-cli-api bridge:

1. Public API receives the question and selected source boxes.
2. API creates a SQLite question row immediately.
3. API writes a compact action prompt for Snoracle that includes question id, selected source types, and the Mission Control JSON answer contract.
4. API calls openclaw agent with --agent <snoracle-agent-id>, --message <prompt>, --thinking xhigh, --timeout <seconds>, and --json.
5. Snoracle performs the actual work: reason about the user question, create meaningful source-specific queries, use subagents/tools for selected data sources, wait for their outputs, and return one structured JSON answer.
6. API captures stdout/stderr, parses or stores the full response, writes SQLite, and returns/dumps the response to the frontend.

Why this solves it:
The model doing the knowledge work is the actual Snoracle agent, not a thin local search harness. This preserves the tuned agent behavior and also avoids the self-route/local-fallback problem from the previous implementation.

Implementation notes:
- Do not use the currently visible human chat route for app output.
- For now, prefer a fresh one-shot OpenClaw agent turn. Add a code/spec comment that persistent Mission Control sessions may be added later with explicit session management.
- Future speed option: add a direct provider/model API path where the user can select model, effort level, and reasoning level. This is not the v1 path.

## Plan 02 - Put The Mission Control Answer Contract In TOOLS.md

Simple explanation:
Snoracle needs a stable instruction for how to answer Mission Control calls. That belongs in TOOLS.md so the full agent turn can read it as local operating context.

Source reason:
David asked for the JSON structured response schema to live in TOOLS.md for testing. The current adapter embeds a small instruction string in code, which is too hidden and too thin for a full agent workflow.

Fix suggest:
Add a Mission Control section to TOOLS.md with the required JSON answer shape, source-box behavior, source-specific query responsibility, citation/label expectations, and candidate/digested decision guidance.

Why this solves it:
The API prompt can stay smaller and cleaner, while Snoracle still sees the answer contract through normal OpenClaw workspace context.

## Plan 03 - Make Source Reasoning An Agent Responsibility

Simple explanation:
Source retrieval should not be hardcoded keyword matching. The agent's job is to understand the question, decide what it needs from WikiLLM, Obsidian, and raw transcripts, and form meaningful source-specific searches or subagent tasks.

Source reason:
The existing worker code tokenizes the question and matches text mechanically. David explicitly rejected that as the core strategy, because the point of using GPT plus OpenClaw is that the agent can reason before querying.

Fix suggest:
Remove the local workers from the primary answer path. In the Snoracle prompt/TOOLS contract, require the agent to restate the research task, decide what each selected source should prove or disprove, generate source-specific queries, use selected-source subagents/tools, and preserve the three source boxes in the final JSON.

Why this solves it:
The source work becomes adaptive and question-aware. This is exactly the layer where an AI agent should add value.

## Plan 04 - Keep CLI Payloads Small And Observable

Simple explanation:
The API should not pass huge evidence blobs as a CLI argument. It should pass an action prompt and let Snoracle/subagents retrieve source material.

Source reason:
Current code proof: _build_openclaw_command() appends the full prompt as --message, while _build_prompt() contains compaction logic and a 180,000 byte soft limit. The answer, evidence, and citation sample limits are local code constants, not configurable settings in config.py. That proves the current design can produce oversized prompts and already works around it by truncating evidence.

Fix suggest:
Use the CLI message only for the action request, source selections, question id, and output contract reminder. If the backend ever needs to provide larger context, write it to kb/mission-control/evidence-packs/ and pass a file path or question id, not the full blob.

Why this solves it:
The command stays stable and avoids OS argument limits. Snoracle can still retrieve or inspect full source material using tools.

## Plan 05 - Do Not Let The API Get Stuck

Simple explanation:
The browser should not hang forever while OpenClaw is running.

Source reason:
The current subprocess call uses capture_output with a long timeout. David also asked for pre/post CLI logging and for the API to dump the response to the frontend so the human handler can review it.

Fix suggest:
Wrap the OpenClaw call in a job runner: log before CLI call, start subprocess with timeout, capture stdout and stderr to per-question log files, store parsed JSON if possible and raw output always, store failure state on timeout/error, and return the stored answer/status to the frontend.

Why this solves it:
The API always has a bounded lifecycle for each request and a readable audit trail when OpenClaw is slow or fails.

## Plan 06 - Hard Stop Flow Is Required But Still TBD

Simple explanation:
Cancellation must eventually stop the active OpenClaw call or session, not only mark the UI cancelled.

Source reason:
openclaw agent --help does not show a cancel flag. openclaw tasks has a cancel command for tracked background tasks, but it is not yet proven that a foreground openclaw agent subprocess creates a cancellable task id. This needs a specific OpenClaw docs/runtime check.

Fix suggest:
For the immediate implementation, track the local subprocess and kill its process group on cancel. Also store any OpenClaw session id or task id if the CLI JSON output exposes one. Research whether OpenClaw agent turns can be cancelled through tasks, sessions, or Gateway APIs, then document the chosen hard-stop path.

Why this solves it:
Local cancellation becomes real immediately, while the OpenClaw-specific stop mechanism is not guessed.

Status:
TBD after OpenClaw cancellation research.

## Plan 07 - HTTPS-Only Public App

Simple explanation:
Port 40006 should serve HTTPS only. HTTP should not return the application.

Source reason:
The current config can fall back to HTTP when TLS files are missing, and allowed origins currently include both HTTP and HTTPS. docs/03-mc.md also still contains old HTTP wording.

Fix suggest:
Require TLS files at startup for public port 40006. If TLS is missing, fail startup instead of serving HTTP. Only allow HTTPS origins for 40006. Keep the self-signed certificate for this stage.

Why this solves it:
The deployed app has one security posture and one public URL. There is no accidental HTTP mode.

## Plan 08 - Hide The Gate From HTML And Browser JS

Simple explanation:
The static gate can remain as a server-side guardrail, but the UI must not advertise it.

Source reason:
The current login HTML renders a visible link containing the gate parameter. David explicitly rejected exposing that literal in HTML/JS.

Fix suggest:
Remove the visible gate link from the login page and do not put the literal gate value in static files. The server can still accept the gate parameter, exchange it for cookies, and redirect to the root page.

Why this solves it:
The guardrail remains functional without training every visitor or scraped HTML copy on the entry URL.

## Plan 09 - Candidate And Digested Flags Replace Wiki Patch Workflow

Simple explanation:
Mission Control should not auto-patch the wiki now. It should only mark useful Q&A as candidates for later digestion.

Source reason:
The current implementation has wiki update candidate and wiki patch job machinery. David wants no workflow yet: just candidate and digested bit columns in SQLite.

Fix suggest:
Add candidate and digested bit columns to the question/Q&A table. Snoracle decides whether an answer is meaningful. If meaningful, the returned JSON or DB write marks candidate = 1. digested starts at 0 and is flipped later by a future digestion workflow. Disable or bypass current automatic wiki patch job creation.

Why this solves it:
The system preserves important answers for later knowledge-base work without pretending to have a safe patch workflow.

Code/spec comment to add later:
Future workflow may review candidate Q&A rows, create proposed wiki diffs, and mark digested = 1 after human or validated automated digestion.

## Plan 10 - Simplify UI Progress For Now

Simple explanation:
Detailed progress telemetry is out of scope for the redesign pass.

Source reason:
David asked to remove the progress-event issue for now and just use a loader.

Fix suggest:
When a query starts, show a loader. When the CLI/API result returns, remove it and render the answer or error. Keep pre/post CLI logs in files for debugging, not as a detailed UI timeline.

Why this solves it:
The UI stays simple while the architecture is being corrected.

## Plan 11 - Obsidian Placeholder Behavior

Simple explanation:
Obsidian does not exist yet, so accidental Obsidian calls should not add noisy text.

Source reason:
The current worker returns 'אין Obsidian עדיין.' David wants an empty string if Obsidian is accidentally called.

Fix suggest:
Until the vault exists, Obsidian source handling should return an empty answer string and an empty evidence list.

Why this solves it:
The three-box answer shape remains possible without polluting every response with placeholder text.

## Immediate Build Order

1. Update TOOLS.md with the Mission Control answer schema and query-reasoning responsibility.
2. Rewrite the adapter into api-cli-api: persist question, call OpenClaw agent, capture/store/dump output.
3. Remove local source workers from the primary answer path; move source work into Snoracle/subagent instructions.
4. Add candidate and digested columns; disable auto wiki patch jobs.
5. Enforce HTTPS-only startup and HTTPS-only origins on 40006.
6. Remove the visible gate link/value from HTML/JS.
7. Simplify frontend progress to loader-on, loader-off.
8. Implement local subprocess cancellation and research the OpenClaw-level hard-stop path.

## Evidence Checked While Rebuilding This Plan

- openclaw agent --help confirms --agent, --session-id, --message, --thinking, --timeout, and --json.
- openclaw sessions --help confirms sessions can be listed and explicit session ids can be targeted by agent turns.
- openclaw tasks --help confirms background tasks have cancel support, but this has not yet been proven for foreground openclaw agent calls.
- Current snoracle_adapter.py passes the whole prompt through --message and has prompt compaction logic.
- Current config.py can fall back to HTTP and allows both HTTP and HTTPS origins.
- Current server.py login page exposes the gate parameter in a visible link.
