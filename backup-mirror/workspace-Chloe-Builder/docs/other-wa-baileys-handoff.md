# other-wa-baileys-handoff.md

## Runtime Topology

- Root: `/opt/wa-y`
- Container: `wa-y`
- Bind: `127.0.0.1:39999:39999`
- Auth persistence: `/opt/wa-y/data/auth:/data/auth`
- Logs: `/opt/wa-y/logs:/logs`
- Restart: `unless-stopped`
- Isolation posture:
  - non-root user in container
  - read-only root filesystem
  - tmpfs for transient writes
  - no mount references to `~/.openclaw`

## Endpoint Map

- Health/lifecycle:
  - `GET /health`
  - `POST /session/connect`
  - `POST /session/disconnect`
  - `POST /session/reconnect`
  - `POST /session/logout`
  - `GET /session/status`
- Pairing/auth:
  - `GET /pairing/qr`
  - `POST /pairing/code`
  - `GET /auth/meta`
- Messaging:
  - `POST /messages/text`
  - `POST /messages/media`
  - `POST /messages/document`
  - `POST /messages/location`
  - `POST /messages/contact`
  - `POST /messages/reaction`
  - `POST /messages/edit`
  - `POST /messages/delete`
  - `POST /messages/read`
- Chat/group:
  - `GET /contacts`
  - `GET /chats`
  - `GET /history/:jid`
  - `POST /groups/create`
  - `GET /groups/:jid/metadata`
  - `POST /groups/:jid/participants`
  - `POST /groups/:jid/subject`
  - `POST /groups/:jid/description`
  - `POST /chats/archive`
  - `POST /chats/mute`
  - `POST /chats/pin`
- Diagnostics/observability:
  - `GET /events`
  - `GET /diagnostics`

## Operational Runbook

- Start/update:
  - `cd /opt/wa-y && docker compose up -d --build`
- Check status:
  - `docker ps --filter name=wa-y`
  - `curl http://127.0.0.1:39999/health`
- Trigger pairing flow:
  - `curl -X POST http://127.0.0.1:39999/session/connect`
  - `curl http://127.0.0.1:39999/pairing/qr`
- QR artifact:
  - `/opt/wa-y/logs/wa-y-qr-latest.png`
- Stop:
  - `cd /opt/wa-y && docker compose down`

## QA Evidence Summary

- Service running:
  - `wa-y Up ... 127.0.0.1:39999->39999/tcp`
- Health endpoint returned:
  - `{"ok":true,"connected":false,"connecting":false}`
- Connect endpoint returned:
  - `{"ok":true,"status":"started"}`
- QR endpoint returned populated `qrDataUrl` and generated PNG file.

## Known Limits

- Some WhatsApp operations require a paired account and valid target JIDs before successful end-to-end execution.
- `/history/:jid` currently exposes a placeholder empty list unless additional store persistence is added.

## Rollback / Recovery

- Stop/remove stack:
  - `cd /opt/wa-y && docker compose down`
- Preserve auth:
  - backup `/opt/wa-y/data/auth` before risky changes.
- Restore:
  - replace `/opt/wa-y/data/auth` with last good backup and restart.
- Never use WA-X credentials or paths for WA-Y recovery.
