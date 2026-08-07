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
- If a David WhatsApp message starts with the emoji 📥, treat it as a hard capture-only signal.
- Copy all text after the emoji into the Google Docs Inbox at https://docs.google.com/document/d/1rFvsRM-NMOINFvti7OgVPzbN2amQmB_ItMU8t6RRtaU/edit?usp=drivesdk as the new first item.
- Do not reinterpret the text after the emoji as an action to perform.
- Do not improvise a different inbox target when that signal appears.
- If the current toolset cannot actually write to Google Docs, say so explicitly instead of marking the capture as completed.

## Operating Protocol

- Use `OPERATING_PROTOCOL.md` as the working ruleset for how to triage, execute, and verify work.
- Keep short-lived chat context separate from durable workspace decisions.
- Prefer the smallest useful file read, edit, and verification step.
- Write reusable workflow decisions into files, not into transient memory.

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
