My take: `docs/sfs-wikillm.md` should be refactored, not just annotated.

`docs/karpathy-wikillm.md` is the source/reference. `docs/sfs-wikillm.md` should become the actual operating spec for the Startup for Startup Hebrew knowledge system.

**Suggestions**

1. Rename the purpose from generic “LLM Wiki” to something specific:
   - Hebrew startup insights wiki
   - based on Startup for Startup transcripts
   - maintained by Snoracle
   - designed for WikiLLM + Obsidian + mission control
user answer: this specific document (`docs/sfs-wikillm.md`) is just for the wiki, do u think we need to do the Obsidian 1st?

Snoracle answer: No. Build the wiki first. The wiki is the knowledge model and operating layer; Obsidian is the human browsing/workspace layer on top of that model. But we should make the wiki Obsidian-compatible from day one: plain markdown, stable filenames, YAML frontmatter, internal links, source citations, and an index/log. So `docs/sfs-wikillm.md` should stay focused on the wiki, while leaving clean interfaces for the later Obsidian vault and mission-control layer.

2. Add the real source paths:
   - raw transcripts: `kb/sources/raw/<videoID>.md`
   - source lists: `kb/sources/lists/`
   - future wiki: probably `kb/wiki/`
   - future Obsidian vault: maybe `kb/obsidian/` or `vault/`

user answer: ok

3. Define the knowledge layers more concretely:
   - raw layer: immutable transcripts
   - source/episode layer: per-video summaries
   - wiki layer: concepts, people, companies mentioned in episodes, playbooks, patterns
   - Obsidian layer: browsable human workspace
   - mission-control layer: Q&A interface over all of the above

user answer: ok

4. Add Hebrew-first rules:
   - generated wiki pages should be in Hebrew
   - keep company/product/person names and key terms in original language when useful
   - explain English startup terms in Hebrew
   - avoid over-translating terms like SaaS, GTM, PMF, AI agent, ARR unless needed

user answer: ok

5. Add page templates:
   - episode/source page
   - person page
   - company page, only for companies mentioned in the podcast corpus
   - concept page
   - startup playbook page
   - recurring pattern page
   - question/synthesis page
   - contradiction/open-question page

user answer: ok


6. Add an ingest workflow:
   - read one transcript
   - create/update episode page
   - extract people, companies, concepts, claims, tactics, examples
   - update existing concept pages
   - create new pages only when they are likely to recur
   - update index/log
   - cite source video IDs

user answer: ok


7. Add a query workflow:
   - answer from wiki first
   - use raw transcripts when explicitly requested or when the wiki is insufficient
   - cite source pages/video IDs
   - distinguish “from source” vs “Snoracle synthesis”
   - save valuable answers back into the wiki

user answer: ok 

8. Add quality rules:
   - no unsupported claims
   - mark uncertainty
   - preserve contradictions between episodes
   - prefer concrete examples from founders/operators
   - separate general startup advice from episode-specific or company-mentioned practice
   - don’t flatten everything into generic startup clichés

user answer: ok 

9. Add taxonomy:
   - fundraising
   - GTM/sales
   - marketing/content
   - product
   - AI adoption
   - agents/workflows
   - startup building
   - founder psychology
   - hiring/org design
   - wartime/emergency management
   - metrics
   - Israeli startup ecosystem

user answer: ok 

Clarification: companies are allowed as source-mentioned items. The podcast corpus is not tied to one specific company, but if an episode discusses a company, that company can become an entity page/item.

10. Add mission-control behavior:
   - when user asks “what does the corpus say?” cite wiki + sources
   - when user asks “show raw data,” quote transcript excerpts
   - when user asks for strategy, synthesize but label it as synthesis
   - when confidence is low, say what source is missing

user answer: ok 

**Questions**

1. Who is the first real user of the system: only you, or other researchers/users too?
user answer: currenlty only me, but with hope for adoption

Snoracle answer: Decision: optimize first for David as the primary user. That means practical workflows, fast iteration, and opinionated defaults are more important than multi-user polish right now. Adoption should be kept possible by avoiding private assumptions inside the generated wiki, keeping citations strong, and making the structure understandable to another researcher later.

2. Should the wiki be entirely Hebrew, or Hebrew body text with English technical terms preserved?
user answer: preserved

Snoracle answer: Decision: Hebrew-first body text, with English technical terms preserved when they are the natural industry term. Examples: SaaS, ARR, GTM, PMF, PLG, AI agent, ICP, churn, retention. The wiki should explain terms in Hebrew when useful, but not force awkward translations.

3. Do you want every episode to have its own page, or should episode pages stay minimal and most value go into concept pages?
user answer: can we do both?

Snoracle answer: Yes. Do both, with different jobs. Every episode gets a source/episode page as the canonical episode dossier. The compounding value goes into concept/entity/playbook pages that synthesize across episodes. Entity pages can include people and companies mentioned by the corpus. Episode pages should preserve provenance; concept pages should accumulate insight.

4. What is the main unit of insight you care about:
   - founder advice
   - tactical playbooks
   - podcast case examples
   - investor/startup ecosystem patterns
   - AI/product/org lessons
   - all of the above?

user answer: anything piece of data items, all of the above, from citations to opinions to your (ai) insights

Snoracle answer: Decision: use a broad evidence-item model. Capture claims, quotes, examples, tactics, frameworks, opinions, stories, metrics, warnings, contradictions, open questions, and Snoracle synthesis. Each reusable item should be source-backed when it comes from the podcast, and clearly labeled when it is AI synthesis.

5. Should the system focus only on “startup insights,” or also include source-specific operating lessons that appear in the podcast?
user answer: no no, we are purely on the podcast as source

Snoracle answer: Decision: source boundary is the podcast corpus only. If source-specific operating lessons appear inside the podcast, they are valid source material, but they should be labeled as podcast-derived and, when relevant, as episode-specific or company-mentioned examples rather than universal startup truth. The podcast has no privileged connection to any specific company. Do not enrich from outside material unless explicitly requested.


6. Do you want citations to use just video IDs, or title + video ID + transcript quote?
user answer: title + video ID + transcript quote + time code + like to vid at that time (exists in the raw data)

Snoracle answer: Decision: citation format should include title, video ID, transcript quote, timecode, and a YouTube timestamp link. Supadata raw data includes offsets/durations, so we can derive approximate timecodes and links like `https://www.youtube.com/watch?v=<videoID>&t=<seconds>s`. The wiki should prefer source-backed claims with this citation format.

7. Should we build a strict Obsidian folder taxonomy now, or let the first batch of wiki pages teach us the right structure?
user answer: idk, reason and websearch and tell be what would be the correct answer

Snoracle answer: Recommendation: do not build a strict deep Obsidian taxonomy now. Use a shallow, stable folder structure plus links, tags, properties, and MOC/index pages. Web search points in the same direction: Obsidian guidance and community practice tend to favor shallow folders, heavy internal linking, MOCs/maps of content, tags/properties for cross-cutting metadata, and avoiding deep nesting. PARA is useful for personal productivity, but this project is a source-backed research wiki, not a personal task system. Correct answer for us: start with minimal folders by page type/layer, then let the first 10-15 processed episodes reveal which concepts deserve durable MOCs or categories.

Suggested initial structure:

- `kb/wiki/index.md`
- `kb/wiki/log.md`
- `kb/wiki/episodes/`
- `kb/wiki/concepts/`
- `kb/wiki/people/`
- `kb/wiki/companies/`
- `kb/wiki/playbooks/`
- `kb/wiki/claims/` or `kb/wiki/evidence/`
- `kb/wiki/questions/`

Use tags/properties for taxonomy terms like `fundraising`, `gtm`, `product`, `ai-adoption`, `founder-psychology`, etc. A note can belong to multiple topics without needing multiple folders.

8. Should mission control answer in a polished research style, or more like a practical startup advisor?
user answer: practical truth teller, no mercy

Snoracle answer: Decision: mission-control voice should be practical, direct, and evidence-grounded. It should avoid consultant polish and say when an idea is weak, generic, unsupported, or contradicted by the corpus. Tone can be blunt, but it still needs source discipline: separate evidence, interpretation, and recommendation.

9. Do we want a “claims database” layer later, where every reusable insight has source backing, confidence, and links to the exact episode/transcript evidence?
user answer: YES

Snoracle answer: Decision: yes, treat the claims/evidence layer as a core future capability, not a nice-to-have. We do not need a database immediately; we can start as markdown files or structured YAML blocks. Each claim should eventually carry: claim text, type, topic tags, source episode, video ID, timecode, quote, confidence, status, related concepts, and whether it is source claim vs Snoracle synthesis.


10. Are raw transcript quotes acceptable as-is, even when Supadata Hebrew transcription has mistakes, or should we create cleaned Hebrew versions too?
user answer: we have no other source for now other than the Supadata transcription, so for now that is the source of truth

Snoracle answer: Decision: Supadata transcript is the source of truth for now. Raw quotes should remain faithful to the transcript, including imperfections. We can create cleaned Hebrew summaries and paraphrases, but they must not replace the raw quote as evidence. If a transcript line looks suspicious, mark uncertainty rather than silently correcting it.

11. My recommendation stays the same: refactor docs/sfs-wikillm.md into a real operating spec, keep docs/karpathy-wikillm.md as the untouched conceptual original.
user answer: yep

Snoracle answer: Decision accepted. Next step should be to rewrite `docs/sfs-wikillm.md` as the concrete wiki operating spec for this project, while keeping `docs/karpathy-wikillm.md` unchanged as the conceptual reference.
