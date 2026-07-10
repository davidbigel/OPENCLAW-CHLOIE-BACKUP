# Mission Control Redesign Mid Report

Date: 2026-07-08

## Short answer

The redesign from `docs/04-redesign-mc.md` is implemented in the codebase and is now verified as the live path on port `40006`.

Before this pass, nothing was listening on `40006` and there was no running Mission Control tmux session. During this pass, Mission Control was brought back up, verified through the public HTTPS app flow, and proven to dispatch a real OpenClaw/Snoracle turn instead of the older local worker path.

## Current live state

- Mission Control is running in tmux session `sfs-mission-control`.
- Public listener is live on `0.0.0.0:40006`.
- Private backend is live on `127.0.0.1:40007`.
- Public transport is HTTPS-only with the existing self-signed cert files under `sfs-mission-control/mission_control/logs/tls/`.

## What is implemented in code

- Real Snoracle bridge:
  - `sfs-mission-control/mission_control/snoracle_adapter.py`
  - Primary path is `openclaw agent --agent wiki-startup-for-startup --session-id <per-question-id> --thinking xhigh --timeout 300 --json`
- HTTPS-only public gate:
  - `sfs-mission-control/mission_control/server.py`
  - `sfs-mission-control/mission_control/config.py`
- Persisted OpenClaw metadata and answer fields:
  - `sfs-mission-control/mission_control/db.py`
  - Stores `openclaw_agent_id`, `openclaw_session_id`, `openclaw_session_key`, `openclaw_run_id`, `openclaw_task_id`, subprocess timing, stdout/stderr/raw paths, `parse_status`, `candidate`, and `digested`
- Layered request handling and cancel plumbing:
  - `sfs-mission-control/mission_control/service.py`
- Frontend loader, polling, rerun, cancel, and raw/parsed rendering:
  - `sfs-mission-control/static/app.js`

The old local workers still exist in the repo as development/test utilities, but they are not the intended primary answer path anymore.

## What was verified live on 2026-07-08

### Public gate behavior

- Unauthenticated `GET /` returned `404`
- Gated/authenticated `GET /` returned the Mission Control HTML shell
- Authenticated `GET /health` returned `200` with JSON status

This matches the redesign requirement that the gate remains server-side and that the public app is not exposed to unauthenticated visitors in a friendly way.

### Real public ask flow

A real authenticated HTTPS `POST /api/ask` was submitted through the public app flow.

Verification question:

- `question_id`: `q_20260708_103108_238636`

Stored OpenClaw execution identity:

- `openclaw_agent_id`: `wiki-startup-for-startup`
- `openclaw_session_id`: `mc-q_20260708_103108_238636-ec3e7798`
- `openclaw_session_key`: `agent:wiki-startup-for-startup:explicit:mc-q_20260708_103108_238636-ec3e7798`
- `openclaw_run_id`: `3589463f-1a9b-49a1-8c64-73cdaf0836c3`
- `openclaw_task_id`: `NULL`

Completion result:

- `status`: `done`
- `parse_status`: `parsed`
- `cli_exit_code`: `0`
- `candidate`: `1`
- `digested`: `0`
- `cli_started_at`: `2026-07-08T10:31:08+00:00`
- `cli_finished_at`: `2026-07-08T10:34:37+00:00`

### Proof that the redesign path was used

The finished question row had:

- populated `openclaw_*` session/run metadata
- saved stdout/stderr/raw-response paths under `sfs-mission-control/mission_control/logs/runs/q_20260708_103108_238636/`
- `source_runs = 0`
- `evidence_items = 0` for that question

That combination matters:

- the populated `openclaw_*` fields prove the backend used the per-question OpenClaw bridge
- `source_runs = 0` for this question proves the answer did not go through the older local per-source worker pipeline

### Saved run artifacts for the verified redesign-path question

Files exist at:

- `sfs-mission-control/mission_control/logs/runs/q_20260708_103108_238636/stdout.txt`
- `sfs-mission-control/mission_control/logs/runs/q_20260708_103108_238636/stderr.txt`
- `sfs-mission-control/mission_control/logs/runs/q_20260708_103108_238636/raw-response.txt`

Observed result:

- `stdout.txt` contains the OpenClaw JSON wrapper with top-level `runId`
- `raw-response.txt` contains the same successful response payload
- `stderr.txt` is empty

## Test and verification results

- `python3 -m unittest discover -s tests -q` => `Ran 16 tests ... OK`
- Public app gate flow verified over HTTPS
- Real end-to-end question completed through the OpenClaw bridge

## Current logs and artifacts available for testing

There is a decent amount of historical Mission Control data, but it is important to separate legacy data from confirmed redesign-path data.

### Confirmed redesign-path artifacts

Confirmed redesign-path volume is still small:

- `1` question with `openclaw_session_id`
- `1` question with `openclaw_run_id`
- `1` question with saved stdout/stderr/raw response files
- `1` question with `parse_status`

So if the goal is specifically to test the new per-question OpenClaw session/run metadata and raw command artifact flow, we currently have only one confirmed live example.

### Historical Mission Control data

Historical volume is larger:

- `11` total questions
- `9` done
- `2` failed
- `160` answer log rows
- `27` source run rows
- `8,985` evidence items
- `7` saved answer snapshots under `sfs-mission-control/mission_control/logs/answers/`

Historical runtime files also include:

- SQLite database: `sfs-mission-control/mission_control/logs/mission-control.sqlite3` at roughly `13 MB`
- server log: `sfs-mission-control/mission_control/logs/server.out`
- app log: `sfs-mission-control/mission_control/logs/app.log`
- multiple smoke-test screenshots in `sfs-mission-control/mission_control/logs/`

### Practical answer about test volume

If David wants to test:

- history UI
- old saved answers
- evidence rendering
- existing database-backed question history

then yes, there is already plenty of legacy data to test against.

If David wants to test:

- the redesigned OpenClaw session/run metadata
- raw stdout/stderr/raw-response artifact capture
- parse-status handling on the new bridge
- candidate/digested persistence on the new bridge

then no, we do not yet have many examples. Right now there is only one confirmed redesign-path run in the database and one corresponding run directory on disk.

## Important caveats

- Browser-tool visual verification was blocked locally because headless Chrome failed to start with `libdl.so.2: Permission denied`.
- API/runtime verification still succeeded, so this did not block verification of the backend behavior.
- I did not re-run a full live cancel-path test during this pass.
- Older question rows mostly predate the redesign, so their `openclaw_*` fields are still `NULL`. That is expected and does not mean the redesign failed.

## Recommended next step if more redesign-path logs are needed

If the next goal is stronger testing coverage for the redesigned path, generate a small batch of fresh live questions through the app, for example:

- `3` normal successful questions with different source combinations
- `1` question that is cancelled mid-run
- `1` question designed to produce weak or malformed output
- `1` longer question to watch timeout behavior if needed

That would quickly turn the current single confirmed redesign-path run into a more useful test set for session/run metadata, raw artifacts, parse-status behavior, and cancellation auditing.
