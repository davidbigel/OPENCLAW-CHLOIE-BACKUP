# OpenClaw NotebookLM Connection Status

Last checked: 2026-08-03 15:21 UTC

## Goal

Allow OpenClaw to operate NotebookLM for `leanagenticai@gmail.com` through the local CLI.

## Existing Implementation

- Workspace: `/root/.openclaw/workspace-GOOG-V1-01-NotebookLM`
- CLI wrapper: `nblm-all`
- OpenClaw helper wrapper: `./nblm-openclaw`
- Backing package: `notebooklm-py[browser,cookies]==0.7.3`
- OpenClaw browser profile: `/root/.chrome-profiles/leanagenticai`

## What Works

- `nblm-all` is installed and responds to `--help`, `capabilities`, and `doctor`.
- The OpenClaw Chrome profile exists and contains Google/NotebookLM cookies.
- The helper wrapper maps the OpenClaw Chrome profile into the path shape expected by `notebooklm-py`.
- Headless Chrome can open `https://notebooklm.google.com` using the OpenClaw profile.

## Current Status

NotebookLM authentication is working for the local CLI.

- Account: `leanagenticai@gmail.com`
- Stored auth: `/root/.notebooklm/profiles/default/storage_state.json`
- Verification: `./nblm-openclaw raw list --json` returned 31 notebooks.
- Temporary login access was provided through noVNC/localhost.run and can be closed after verification.

## Previous Blocker

The OpenClaw Chrome profile was no longer authenticated enough for NotebookLM.

Observed result before re-authentication:

```text
STALE_COOKIES
```

The browser lands on:

```text
Sign in - Google Accounts
```

## How To Run

```bash
cd /root/.openclaw/workspace-GOOG-V1-01-NotebookLM
./nblm-openclaw status
./nblm-openclaw inspect-browser
./nblm-openclaw bootstrap
```

Useful commands:

```bash
./nblm-openclaw raw list --json
./nblm-openclaw refresh
```
