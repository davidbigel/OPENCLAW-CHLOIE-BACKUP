# Project Resume Prompt

When David wants to resume a paused project later, he can send a message like this:

> Resume the [project name] project from the last saved handoff.
> Read the handoff file and the linked working docs first.
> Reconstruct the current state, the goal, the important decisions, and the open questions.
> Do not restart from scratch unless the handoff is missing.
> Tell me:
> 1. what you understand the project to be
> 2. what was already completed
> 3. what is still open
> 4. what the next best step is
> Then continue from there.

## What Chloe should do on receiving it

1. Find the project handoff file.
2. Read the handoff and the linked working docs.
3. Rebuild the project state from the saved files.
4. Summarize the current state back to David in short form.
5. Ask one short question only if a critical detail is missing.
6. Resume from the next best step, not from the beginning.

## What makes the resume reliable

Include these details in the resume message:
- project name
- last completed step
- paused status
- handoff file name
- linked working files
- desired next step
- any things that should not be repeated

## Good resume pattern

"Resume OKF from `OKF-PROJECT-HANDOFF.md`. Current docs are `OKF-OPERATING-MODEL.md`, `OKF-DAILY-CHECKLIST.md`, and `OKF-IMPLEMENTATION-ROADMAP.md`. Do not restart the research. Reconstruct the state and continue from the next best step."


