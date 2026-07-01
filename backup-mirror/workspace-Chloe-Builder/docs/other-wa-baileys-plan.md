# other-wa-baileys-plan.md

## Objective

Build and run a second, fully isolated Dockerized Baileys runtime for WhatsApp number **Y**, controlled by a separate OpenClaw agent, while leaving OpenClaw's existing WhatsApp runtime for number **X** untouched.

Success target:
- the `wa-y` Docker service is running in isolation on `127.0.0.1:39999`
- auth state persists across restarts
- the service can propose QR/pairing output for linking phone Y

## Hard Constraints

- Do not test, probe, or modify OC host WA-X behavior.
- Keep all WA-Y implementation isolated from `~/.openclaw` internals.
- Use port `39999`.
- Expose full Baileys operation surface (A-Z), not a minimal subset.
- Execute step-by-step with ACP Codex coding agents plus separate QA subagents per step.
- Keep all intermediate and final execution state tracked in persistent TODO/state files.

## Target Topology

- Project root: `/opt/wa-y`
- Container: `wa-y`
- Bind: `127.0.0.1:39999:39999`
- App port: `39999`
- Persistent auth mount: `/opt/wa-y/data/auth:/data/auth`
- Logs mount: `/opt/wa-y/logs:/logs`
- No mounts from `~/.openclaw`
- Restart policy: `unless-stopped`
- Non-root runtime
- Read-only root FS where feasible + `tmpfs` for transient writes

## API Surface (A-Z Coverage)

The controller-facing API must cover:

- Session lifecycle:
  - connect, disconnect, reconnect, logout
  - socket and connection state

- Pairing/auth:
  - QR retrieval
  - pairing-code retrieval (if supported)
  - auth/session metadata endpoints

- Messaging:
  - send text
  - send media (image/video/audio)
  - send document
  - send location and contacts
  - reactions
  - edit/delete where supported
  - read/receipt operations

- Chat and group operations:
  - group create
  - group metadata read
  - participant add/remove/promote/demote
  - subject/description updates
  - chat archive/mute/pin controls where supported

- Retrieval and diagnostics:
  - contacts/chats listing
  - history retrieval hooks
  - event stream/webhook output
  - reconnect counters
  - last error + raw diagnostics

## Implementation Sequence

### Step 1 - Create persistent execution TODO/state system (required first)

Create and maintain state files before coding runtime changes:

- `docs/other-wa-baileys-execution-todo.md`
  - per-step checklist
  - owner agent per task
  - current status (`pending`, `in_progress`, `qa_failed`, `qa_passed`, `done`)
  - blockers and next actions

- `docs/other-wa-baileys-execution-state.json`
  - machine-readable state for continuity across sessions/compactions
  - fields: `current_step`, `attempt`, `last_coder_agent`, `last_qa_agent`, `qa_result`, `artifacts`, `updated_at`

Rules:
- Update both files at every step transition.
- Update both files before and after every coder/QA subagent run.
- Resume from these files after any interruption or context compaction.

### Step 2 - Scaffold WA-Y runtime baseline

- Create `/opt/wa-y` directory tree.
- Add compose file, env file, app skeleton, auth/log directories.
- Configure container defaults for isolation and restart behavior.

### Step 3 - Implement Baileys socket bootstrap + auth persistence

- Initialize Baileys client runtime.
- Persist auth in `/data/auth`.
- Handle reconnect and lifecycle transitions cleanly.

### Step 4 - Implement full A-Z API surface + validation

- Implement documented endpoint groups for lifecycle, pairing, messaging, group ops, retrieval, diagnostics.
- Add strict input validation and structured error responses.

### Step 5 - Implement event stream, observability, and diagnostics

- Add webhook/event stream emission for agent controller.
- Add structured logs and diagnostic endpoints.
- Record reconnect/error counters and last-error details.

### Step 6 - Harden container isolation and runtime posture

- Enforce localhost-only bind (`127.0.0.1:39999`).
- Non-root execution.
- Read-only root filesystem where feasible.
- Writable mounts only where required (`/data/auth`, logs, temp).

### Step 7 - Validate functionality and persistence (without touching WA-X)

- Verify container health and local reachability.
- Verify endpoint availability across full surface.
- Verify restart persistence (no forced re-pair).
- Verify QR/pairing endpoint output is generated for phone Y.

### Step 8 - Final handoff artifact creation (last step)

Create `docs/other-wa-baileys-handoff.md` as final handoff output for the controller/operations agent, including:
- runtime topology
- endpoint map
- operational runbook
- known limits
- QA evidence summary
- rollback and recovery instructions

This handoff generation must be the final implementation step.

## Required Execution Loop Per Step

For every step (Steps 1-8):

1. Spawn ACP Codex coding agent for that step implementation only.
2. Spawn separate QA subagent to verify that exact step.
3. If QA fails:
   - spawn ACP Codex coding agent for fixes
   - re-run QA subagent
   - repeat until QA passes
4. Mark step complete in TODO/state files only after QA pass.
5. Move to next step.

## QA Gates

Minimum gate before declaring done:

- No OC WA-X runtime tests performed.
- WA-Y isolated service bound only to `127.0.0.1:39999`.
- Full A-Z endpoint surface reachable (or clearly marked unsupported-by-Baileys with rationale).
- Auth persists across restart.
- QR/pairing output available for linking phone Y.
- Execution TODO/state files are complete and consistent.
- Final handoff file produced in Step 8.

## Rollback

- Stop/remove only `wa-y` stack.
- Preserve `/opt/wa-y/data/auth` backup before major changes.
- Restore auth from last known good backup if corruption occurs.
- Never use OpenClaw WA-X credential paths for WA-Y recovery.

## Done Criteria

This plan is complete only when all steps have QA pass evidence and Step 8 handoff file has been generated as the final artifact.
