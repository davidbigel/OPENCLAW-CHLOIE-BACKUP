# Operating Runbook

## 1. Classify the request

- capture: preserve the text and route it to the correct durable place.
- question: answer directly from the smallest reliable source.
- task: perform the action, then verify it.

## 2. Pick the source of truth

- Use the current conversation for immediate context.
- Use workspace files for durable behavior and decisions.
- Use memory files for long-term lessons and patterns.

## 3. Execute

- Read only what is necessary.
- Edit with apply_patch.
- Keep each change narrow and reversible.

## 4. Verify

- Run a targeted check or inspect the diff.
- If verification fails, report the failure plainly.

## 5. Report

- State the outcome first.
- Mention only the files changed and the meaningful result.
- Suggest a next step only if it is naturally useful.
