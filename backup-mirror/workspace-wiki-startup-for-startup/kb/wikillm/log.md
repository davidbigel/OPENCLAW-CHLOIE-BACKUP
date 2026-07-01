---
type: log
status: active
---

# WikiLLM Log

## [2026-06-30] maintenance | create product root | kb/wikillm

- Created root product structure under kb/wikillm per David's instruction.
- Used docs/karpathy-wikillm.md as conceptual context.
- Used docs/sfs-wikillm.md as operating prompt, with path override from kb/wiki to kb/wikillm.

## [2026-06-30] ingest | pilot batch | 3 episodes

- Processed:
  - LDhEAG9lxR0 - 355: How We Recreated Our Podcast in English Using AI
  - pRtCeFZFm1M - 353: איך בנינו ״מוח צוותי״ שמתעדכן לבד
  - PZpLqSjlfGw - 352: The Agent Lab: How We Built a Playground for the Next AI Product
- Created episode pages, concept pages, people pages, playbooks, claims index, and a pilot synthesis question.
- Claims added:
  - AI localization expands existing content to new languages but still needs human review.
  - A persistent LLM Wiki compounds knowledge better than question-time retrieval alone.
  - Team context systems fail when they become personal workflows instead of shared infrastructure.
  - Fast AI experimentation should be measured by real usage/value, not only technical novelty.
  - Organizational AI adoption lags behind technical capability.
- Open questions:
  - How much should the wiki normalize bad Hebrew transcript text versus preserve exact source quotes?
  - Should claims become one file per claim after the pilot, or stay grouped until volume grows?
  - Should company pages be created only when a company is central to an episode, or whenever a company is mentioned?

## [2026-06-30] ingest | full corpus draft | 35 episodes

- Expanded WikiLLM from 3-episode pilot to full-corpus draft.
- Generated missing episode pages under kb/wikillm/episodes.
- Rebuilt kb/wikillm/index.md to include all 35 episodes.
- Created/updated auto-generated concept, people, company, playbook, and evidence-register pages.
- Excluded Monday.com from generated company entities per project boundary; original source titles/quotes remain unchanged.
- Preserved curated pilot pages unless absent.
