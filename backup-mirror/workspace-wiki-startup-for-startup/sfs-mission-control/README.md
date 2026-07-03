# SFS Mission Control

Local mission-control app for the Startup for Startup WikiLLM project.

## Run

    python3 -m mission_control.server

Default endpoints:

- Public UI: https://localhost:40006/
- External UI target: https://187.124.10.241:40006/
- Private backend: http://127.0.0.1:40007

Runtime TLS files are required at `kb/mission-control/tls/public.crt` and
`kb/mission-control/tls/public.key`; port 40006 is HTTPS-only.

The public gate remains a server-side v1 guardrail. Do not expose its literal value in HTML or browser JavaScript. The browser never receives OpenClaw, Supadata, LLM, or Gateway secrets.

## Snoracle Dispatch

The app uses `mission_control/snoracle_adapter.py` as the only bridge to Snoracle.

Modes:

- `MC_SNORACLE_MODE=openclaw` - calls `openclaw agent --agent wiki-startup-for-startup --session-id <per-question-id> --thinking xhigh --timeout 300 --json`. This is the default.
- `MC_SNORACLE_MODE=local` - deterministic local response, useful for development and tests only.
- `MC_SNORACLE_AGENT_ID` - explicit OpenClaw agent id override. Production should keep `wiki-startup-for-startup`.
- `MC_SNORACLE_TIMEOUT_SECONDS` - per-turn OpenClaw timeout; default `300`.

Default: OpenClaw, with raw stdout/stderr stored even when JSON parsing fails.

## Data

Runtime data is stored under:

- SQLite: kb/mission-control/mission-control.sqlite3
- Logs: kb/mission-control/logs/
- OpenClaw run output: kb/mission-control/runs/<question_id>/
- Candidate/digested flags: stored on each question row; no automatic wiki patch job runs in this phase.
