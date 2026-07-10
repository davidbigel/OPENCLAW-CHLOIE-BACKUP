# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## WhatsApp Delivery Notes

- Always include `channel: "whatsapp"` when using the `message` tool for delivery.
- For audio, convert to WhatsApp-friendly formats first; prefer `.m4a` and `.ogg`.
- When sending audio as a voice note, use `asVoice: true`.
- Use `forceDocument: true` for files that should not be compressed by WhatsApp.
- Do not rely on `mediaUrl` in RPC flows; place files under `/root/.openclaw/workspace/`, `/root/.openclaw/media/`, or `/tmp/.openclaw/`.
- Keep files under the 50 MB default size limit.
- Supported payloads include images, video, audio, PDF, Office docs, Markdown, TXT, JSON, YAML, and YML.

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

## Related

- [Agent workspace](/concepts/agent-workspace)
