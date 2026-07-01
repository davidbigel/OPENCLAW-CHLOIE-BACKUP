# other-wa-baileys.md

## Goal

Run a second, fully isolated Baileys-based WhatsApp runtime for phone number **Y**, while OpenClaw keeps using its own WhatsApp runtime for phone number **X**.

The second runtime must:
- not share process, auth state, credentials, or config with OpenClaw
- be controllable by a separate agent in this OpenClaw workspace
- be easy to stop/rebuild without touching OpenClaw's primary WA channel

## Current Best-Practice Notes (Baileys)

- Baileys is linked-device based (not official WhatsApp Business API/WABA Cloud).
- Latest major versions have breaking changes; pin dependency version explicitly.
- `useMultiFileAuthState` is useful for bootstrap/demo, but durable auth/key storage should be treated carefully in production.
- Keep auth state on persistent storage and never share it across two runtimes.

## Target Architecture (Recommended)

Use **Dockerized sidecar service** for the secondary Baileys runtime.

Isolation boundaries:
- dedicated container (`wa-y`)
- dedicated persistent volume for auth/session (`wa-y-auth`)
- dedicated bind/network/port (localhost only)
- separate env file (`.env.wa-y`)
- separate systemd/docker lifecycle from OpenClaw

Control path:
1. Agent in OpenClaw calls a small local HTTP API exposed by `wa-y` (localhost only).
2. API exposes full operational surface needed to drive Baileys end-to-end (not minimal subset).
3. No direct access from `wa-y` to OpenClaw credential directories.

## Directory Layout

Create a separate project directory, for example:

\`\`\`
/opt/wa-y/
  docker-compose.yml
  .env.wa-y
  app/
    package.json
    src/index.ts
  data/
    auth/              # persisted Baileys auth/key state
  logs/
\`\`\`

## Implementation Plan

1. Prepare runtime
- Install/verify Docker + Compose.
- Create `/opt/wa-y` tree and file ownership.
- Create an internal Docker network (or use compose default).

2. Build full-surface Baileys API service
- Node 20+ base image.
- Dependencies: `@whiskeysockets/baileys`, `express`, `pino`.
- Expose complete operation set as explicit HTTP actions (A-Z coverage for agent use):
  - session lifecycle: connect, disconnect, reconnect, logout
  - pairing/auth: QR retrieval, pairing code retrieval, session state inspection
  - messaging: send text, media, document, location, contacts, reactions, edits, delete
  - chat ops: read receipts, presence, typing, mute/archive/pin controls where supported
  - group ops: create, metadata, participants add/remove/promote/demote, subject/description updates
  - fetch ops: chats, contacts, message history, media download hooks
  - webhook/event stream: inbound message and event feed for controller agent
  - diagnostics: raw event logs, socket state, last error, reconnect counters
- Persist auth keys in `/data/auth`.

3. Hard isolation controls
- Bind service to `127.0.0.1:39999` only.
- Run container as non-root.
- Read-only root filesystem where possible.
- Mount only `/opt/wa-y/data/auth` writable.
- Avoid sharing `/root/.openclaw` mounts.

4. Pair number Y
- Start service.
- Trigger pairing code/QR.
- Scan from phone **Y** via Linked Devices.
- Success condition for this project: Dockerized service reliably proposes QR/pairing for phone Y.

5. Agent integration
- Add local tool wrapper (or script) that calls `http://127.0.0.1:39999`.
- Teach controller agent full Baileys operation model (A-Z) and endpoint mapping.
- Assign a dedicated agent/session for controlling number Y to avoid policy bleed with number X flows.

6. Reliability
- Add restart policy (`unless-stopped`).
- Add log rotation.
- Add periodic status check (cron or heartbeat note).

## Execution Method (Required)

The plan executor must run implementation as a strict step loop:
1. For each step, spawn an ACP Codex coding agent to implement only that step.
2. After implementation, spawn a separate QA subagent to verify that step.
3. If QA fails:
   - spawn Codex again for focused fixes
   - re-run QA subagent
   - repeat until step passes.
4. Proceed to next step only when current step is green.
5. Continue until full plan completion and QR/pairing proposal success is reached.

## Example Compose Skeleton

\`\`\`yaml
services:
  wa-y:
    image: node:20-alpine
    container_name: wa-y
    working_dir: /app
    command: ["node", "dist/index.js"]
    restart: unless-stopped
    ports:
      - "127.0.0.1:39999:39999"
    environment:
      - PORT=39999
      - AUTH_DIR=/data/auth
      - LOG_LEVEL=info
    volumes:
      - /opt/wa-y/app:/app:ro
      - /opt/wa-y/data/auth:/data/auth
      - /opt/wa-y/logs:/logs
    read_only: true
    tmpfs:
      - /tmp
    user: "1000:1000"
\`\`\`

Note: if runtime needs write access for compiled artifacts, switch to baked image flow instead of read-only app mount.

## QA Checklist (Before Declaring Done)

- Do not test or probe OpenClaw host WA-X runtime.
- `wa-y` container healthy and reachable only at `127.0.0.1:39999`.
- QR or pairing code endpoint returns usable output for phone Y.
- Full operation surface responds (lifecycle, messaging, groups, fetch, diagnostics).
- Restart container; auth persists; no re-pair required.
- No `wa-y` writes outside `/opt/wa-y` mounts.

## Rollback / Recovery

- Stop and remove only `wa-y` container and its compose stack.
- Keep `/opt/wa-y/data/auth` backup tar before major upgrades.
- If auth corruption occurs, restore last-good auth backup and restart.
- Do not reuse OpenClaw WhatsApp credential directories for recovery.

## Optional Next Step

If you want stricter blast-radius isolation, run `wa-y` on a lightweight VM or separate host and expose only a private tunnel/proxy endpoint to this machine.
