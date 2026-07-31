# WhatsApp /new Session Reset Spec

## Problem

When the user sends /new in WhatsApp, the message should not be handled as plain chat text. It should trigger OpenClaw's session reset flow and begin a fresh session for that chat.

## Root cause

The current OpenClaw config in this workspace was missing the DM isolation setting needed for WhatsApp direct chats, and the session reset trigger declaration was not explicit enough for the intended behavior. As a result, /new could be routed into the shared DM session path instead of behaving like a clean fresh chat reset.

## Desired behavior

- /new starts a fresh session.
- /reset remains the alias for session reset.
- Bare /new and /reset are intercepted before agent dispatch.
- The command should not be treated as ordinary agent input.

## Implementation

Update the root OpenClaw config to declare:

- session.scope = "per-sender"
- session.dmScope = "per-channel-peer"
- session.resetTriggers = ["/new", "/reset"]

This aligns the WhatsApp channel with the documented OpenClaw session command path.

## Validation

After restart, verify:

1. Sending /new in WhatsApp opens a fresh session.
2. Sending /reset resets the current session.
3. Normal messages still stay in the current session.
4. No duplicate agent reply is generated for the bare reset command.

## Notes

If /new <model> is used, OpenClaw should still respect the documented model-switch behavior.
