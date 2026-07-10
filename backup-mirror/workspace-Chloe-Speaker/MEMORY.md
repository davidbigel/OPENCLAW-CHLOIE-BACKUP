# memory


you are part of that trio:
1. Chloe-Speaker - YOU. the one David talks directly via whatsapp business number. that is the agent interacting with the human, low permissions.
2. Chloe-Builder - the high permissions one, when human David wants to actually do and build something in this host, he is the worker
3. Chloe-Private-WA -  has its own Baileys internal platform to operate David human private whatsapp. 

use `sessions.send` tool to communicate with them when needed and always respond in the whatsapp channel with their responses.

When David asks me to create or store files, save them in `/root/.openclaw/workspace-Chloe-Speaker/DAVID/` by default unless he says otherwise.

David's preferred conversation mode is "ping pong": keep prompts and replies short, answer with a compact structure, use numbered lists when they improve readability, and use emojis when they add useful context.

Startup for Startup / Monday AI episode set:
- The recurring thesis across episodes 337, 338, 339, 340, 343, 345, 346, 347, 348, 350, 351, 352, 353, and 355 is that Monday is shifting from "managing work" to "doing the work" with AI agents.
- The org-wide pattern is: start with small internal wins, prove value fast, and expand from copilot-style helpers to autonomous agent workflows.
- Repeated themes include: agents as first-class users, team memory / context systems, democratized data access, sales and support agents, change management, security guardrails, and using the public market pressure as a forcing function.
- Notable internal projects mentioned in the summaries: Agent Labs, Spike, Sherlock, Morpheus, Kramer, Amanda/Jax/Oscar/Zoe, Agent Week, Team Brain, and the English localization of the podcast with AI voice clones.

Customer Requirement project:
- Created a dedicated intake workflow under /root/.openclaw/workspace-Chloe-Speaker/DAVID/customer-requirement for turning voice notes into developer-ready requirement specs.
- Standard folder contract: 00_raw, 01_transcripts, 02_requirements, 03_questions, 04_final, 05_runs, 99_archive.
- Operating rule: never overwrite raw inputs; keep versioned drafts; save audit logs for each run; archive superseded artifacts.
- The first captured use case is a reusable wiki/LLM knowledge-base agent, with MVP 1 focused on Startup for Startup and MVP 2 on organization meeting knowledge bases.
