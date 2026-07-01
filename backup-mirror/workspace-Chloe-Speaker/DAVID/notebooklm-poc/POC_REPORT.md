# NotebookLM POC Report

Date: 2026-06-11

## Goal

Validate whether NotebookLM can be controlled from OpenClaw via CLI/MCP well enough to justify a fuller agent implementation.

## Environment

- Workspace: `/root/.openclaw/workspace-Chloe-Speaker/DAVID/notebooklm-poc/`
- Node: `v22.22.2`
- npm: `10.9.7`
- Python: `3.12.3`
- pip: `26.1.2` inside venvs
- uv: not installed

## Primary Tool Chosen

- Tool: `notebooklm-mcp-cli`
- Version tested: `0.7.2`
- Install method: Python virtualenv + `pip install notebooklm-mcp-cli`

### Why this tool was chosen

It directly exposes both a CLI and MCP server, matched the requested architecture best, installed cleanly, and surfaced the exact notebook/source/query operations needed for the POC.

## Fallback Tool Checked

- Tool: `notebooklm-py`
- Version tested: `0.7.1`
- Install method: separate Python virtualenv + `pip install notebooklm-py`

### Why fallback was checked

The primary tool was blocked on authentication, so one fallback was checked exactly as requested.

## Authentication Findings

### notebooklm-mcp-cli

- `nlm login --check` failed because no default auth profile existed.
- `nlm doctor` reported:
  - profile missing / not authenticated
  - Google Chrome installed
  - headless auth not available because no saved profile exists
  - explicit instruction to run `nlm login` once
- The tool's documented auth path is browser-based login or cookie import.

### notebooklm-py

- `notebooklm doctor` with a clean fallback home showed `not authenticated`.
- `notebooklm auth inspect` found no valid Google auth cookies.
- `notebooklm login --browser-cookies chrome` failed with:
  - `can't find cookies file`
- Its normal auth flow also requires browser login.

### Browser/session state

- No running user Chrome/Chromium/Brave/Edge process was present during the test.
- OpenClaw browser integration itself was not usable in this environment during the run:
  - `openclaw_browser start` and `openclaw_browser open` timed out with
    `Restart the OpenClaw gateway`

## Actions That Worked

- Created isolated POC workspace directory.
- Installed and ran `notebooklm-mcp-cli`.
- Verified `nlm --version` and `nlm --help`.
- Verified relevant command surface exists for:
  - list notebooks
  - create notebook
  - rename notebook
  - add source
  - query/chat
- Verified advanced capability discovery from CLI help for:
  - research
  - audio overview
  - video overview
  - mind map
  - report
  - quiz
  - flashcards
  - infographic
  - data table
  - sharing
  - download/export artifacts
- Installed and evaluated one fallback tool: `notebooklm-py`.

## Actions Not Performed

These were intentionally not performed because authentication never succeeded:

- list real notebooks
- create test notebook
- rename test notebook
- add test source
- run query/chat against a notebook
- cleanup/delete notebook

## Failures / Blockers

1. No authenticated Google browser session or reusable NotebookLM cookies were available.
2. Both tools ultimately require a browser-backed auth step.
3. OpenClaw browser start/open timed out at the gateway level, so that path could not be used as an external CDP provider during this run.

## Stability Assessment

- CLI installation stability: medium-high
- Auth path stability in this environment: low
- End-to-end POC readiness in current environment: low

## POC Outcome Against Success Criteria

Success criteria met:

1. CLI works locally: yes
2. Auth to NotebookLM succeeds: no
3. Can read notebook list: no
4. Can create/rename notebook or add source: no
5. Can chat/query successfully: no

Result: 1/5 criteria met

## Recommendation

Do not proceed to a full agent yet.

Recommended next step:

1. Fix the browser/auth prerequisite first:
   - either provide a running browser session already authenticated to Google/NotebookLM
   - or perform one manual `nlm login` on the target machine
2. Also fix the OpenClaw browser gateway timeout if the intended auth strategy is CDP/OpenClaw-managed browser.
3. After auth is in place, rerun the same POC flow. The command surface looks sufficient for a meaningful second pass.

## Bottom Line

The control surface appears promising, but this run could not prove notebook operations because the environment lacked a usable authenticated Google session and required a manual browser login step.
