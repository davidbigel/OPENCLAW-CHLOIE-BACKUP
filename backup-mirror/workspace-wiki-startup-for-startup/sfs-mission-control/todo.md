# SFS Mission Control Todo

## Work Log

- 2026-06-30 17:40 UTC - Started implementation under `sfs-mission-control/`.

## Pre-Audit

- [x] Read `docs/03-mc.md` end to end.
- [x] Read `docs/03-mc-grill.md`; no open questions remain.
- [x] Confirmed Python 3.12 and `rg` are available.
- [x] Confirmed OpenClaw CLI exists; exact persistent dispatch will be isolated behind an adapter.

## Tasks

- [x] Create project folder and this todo/work log.
- [x] Scaffold Python package, static UI folders, and docs.
- [x] Implement SQLite schema and persistence layer.
- [x] Implement logging and app configuration.
- [x] Implement source workers: WikiLLM, Raw Sources, Obsidian unavailable.
- [x] Implement Snoracle synthesis/dispatch adapter with local fallback and OpenClaw CLI mode.
- [x] Implement public/private HTTP servers on 40006/40007.
- [x] Implement auth gate, cookie, CSRF, same-origin checks, and private API secret.
- [x] Implement frontend UI with history/nav, source toggles, loading state, source boxes, citations popup.
- [x] Implement cancellation, rerun, saved thread controls.
- [x] Implement meaningful-answer markdown snapshots.
- [x] Implement serialized wiki patch job queue.
- [x] Run self-audit before execution tests.
- [x] Run automated tests and compile checks.
- [x] Start local server and verify UI/API.
- [x] Run browser visual smoke test.
- [x] Patch post-audit implementation gaps.
- [x] Run post-implementation self-audit.
- [x] Spin QA + code review agent and record result.
- [ ] Fix QA blocker: forgeable/non-expiring auth cookie.
- [ ] Fix QA blocker: cancellation can be overwritten by final completion.
- [ ] Fix QA blocker: wiki patch queue falsely marks no-op jobs done.
- [ ] Fix QA issue: OpenClaw dispatch payload can exceed CLI argument limits.
- [ ] Fix QA issue: progress telemetry is too thin.
- [ ] Fix QA issue: final JSON can overwrite complete SQLite evidence.
- [ ] Fix QA issue: duplicate proxied Server/Date headers.
- [ ] Add focused regression tests for QA blockers.
- [ ] Address remaining QA findings or document why not.
- [ ] Final report to David.

## Audit Notes

- Pre-audit risk: OpenClaw persistent-session dispatch details are not stable enough to leak into app code. Mitigation: one `snoracle_adapter` module owns all OpenClaw CLI/Gateway interaction and the rest of the app consumes structured JSON only.
- Pre-audit risk: exposing port 40006 publicly with static `?p=3d20` is weak auth. Mitigation: exchange query string for HttpOnly cookie, enforce CSRF and origin checks, keep 40007 localhost-only.
- Pre-audit risk: source workers can return too much raw evidence. Mitigation: store all matches, render expandable quotes, and keep summary separate from evidence table.
- Self-audit before tests: file structure and source-routing match the spec. Caveat: local fallback does not invent wiki patch candidates; patch jobs are created when Snoracle/OpenClaw returns wiki_update_candidates.
- Automated checks: python3 -m compileall -q mission_control tests passed.
- Automated checks: python3 -m unittest discover -s tests -v passed, 3 tests.
- Runtime check: app started on 40006/40007 in local Snoracle mode.
- Runtime check: auth gate returned the UI, CSRF was issued, POST /api/ask accepted a real question, workers completed, response reached done status.
- Runtime check: private 40007 rejected a request without the internal secret; public POST without CSRF was rejected.
- Self-audit finding: static/app.js had a malformed citation link string and failed node --check. Fixed before browser smoke testing.
- Browser visual smoke: OpenClaw browser start failed, so I used Playwright Chromium. Auth redirect, UI render, question submit, SSE/polling, WikiLLM/Raw used, Obsidian unavailable, and screenshot smoke all passed.
- Post-audit finding: UI did not yet expose answer logs/progress, history badges were thin, Enter-to-submit was missing, MC_SNORACLE_SESSION_KEY was not supported, and wiki update candidates were not inserted into their own table. Patching these before final QA.
- Visual audit note: screenshot was readable with no overlap, but progress timestamps were cramped in RTL/LTR flow. Adjusted progress-log timestamp layout.
- Post-audit fixes completed: progress log, source badges, thread marker, Enter submit, MC_SNORACLE_SESSION_KEY alias, wiki update candidate persistence, and extra tests are in place.
- Automated checks after post-audit fixes: node --check passed; python3 -m compileall passed; unittest passed with 4 tests.
- Runtime smoke after post-audit fixes: Playwright submitted via Enter key and reached done with 12 progress events, WikiLLM used, Raw used, and Obsidian unavailable as expected.
- Secret scan: no browser-exposed OpenClaw, Supadata, Gateway, LLM, or API tokens found. Only expected static v1 gate, test secrets, and server-side config names appear.
- QA/code-review agent result: FAIL for public/runtime readiness. High blockers: forgeable/non-expiring auth cookie, cancellation race, misleading no-op wiki patch queue, default local Snoracle mode vs persistent Snoracle spec. Medium findings: brittle OpenClaw CLI payload for raw-heavy questions, incomplete progress telemetry, incomplete structured citation parsing, final JSON can overwrite full evidence, duplicate proxied headers, missing tests.
