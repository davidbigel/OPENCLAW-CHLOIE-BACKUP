# NotebookLM CLI

This workspace now ships a local CLI wrapper named nblm-all, backed by notebooklm-py.

It exposes the full upstream NotebookLM surface through nblm-all raw ..., plus a couple of local helpers:

- nblm-all capabilities
- nblm-all doctor
- nblm-all auth-bootstrap --email leanagenticai@gmail.com ...
- nblm-all access-account --email leanagenticai@gmail.com --json

## Setup

    python3 -m venv .venv
    . .venv/bin/activate
    pip install -U pip setuptools wheel
    pip install -e .

## Usage

Inspect the supported feature families:

    nblm-all capabilities

Run any upstream NotebookLM command:

    nblm-all raw list --json
    nblm-all raw create "Research Notebook" --use
    nblm-all raw source add --url https://example.com
    nblm-all raw ask "Summarize the current notebook"
    nblm-all raw generate audio

Authenticate with browser cookies when this machine already has a signed-in Chrome profile:

    nblm-all auth-bootstrap --email leanagenticai@gmail.com --browser-cookies chrome --json

Or fall back to interactive browser login:

    nblm-all auth-bootstrap --email leanagenticai@gmail.com --interactive

If you already have a Playwright storage-state file:

    nblm-all auth-bootstrap --email leanagenticai@gmail.com --storage-state /path/to/storage_state.json --json

If you already have inline auth JSON saved to a file:

    nblm-all auth-bootstrap --email leanagenticai@gmail.com --auth-json-file /path/to/auth.json --json

Then list all notebooks for the authenticated account:

    nblm-all access-account --email leanagenticai@gmail.com --json
