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

The app uses mission_control/snoracle_adapter.py as the only bridge to Snoracle.

Modes:

- MC_SNORACLE_MODE=openclaw - calls openclaw agent --session-id <id> --thinking xhigh --json. This is the default.
- MC_SNORACLE_MODE=openclaw - calls openclaw agent through the current Snoracle agent route. By default it targets the current agent's persistent main session via --agent <id>.
- MC_SNORACLE_MODE=local - deterministic local synthesis fallback, useful for development and tests.
- MC_SNORACLE_AGENT_ID - explicit OpenClaw agent id override.
- MC_SNORACLE_SESSION_ID - explicit OpenClaw session UUID override when you need to pin a concrete stored session.
- MC_SNORACLE_SESSION_KEY - compatibility input. If set to agent:<id>:main it is parsed into MC_SNORACLE_AGENT_ID; raw session-like labels are not passed to the CLI.

Default: openclaw, with local fallback if dispatch fails.

## Data

Runtime data is stored under:

- SQLite: kb/mission-control/mission-control.sqlite3
- Logs: kb/mission-control/logs/
- Meaningful answer snapshots: kb/mission-control/answers/
