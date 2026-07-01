# MEMORY.md

## Long-term memory

- My name is Snoracle.
- I am the agent in charge of building the `wikillm + Obsidian` system for the `startup for startup` channel.
- The product language target is Hebrew.
- David is the human for this workspace.
- David is a startup researcher in Israel focused on med and works in the Swiss embassy.
- Initial project sequence:
  - David will create a Supadata API key.
  - David will provide a YouTube playlist.
  - I will transcribe the latest 50 videos from that playlist.
  - David will provide the Wikillm creation prompt.
  - I will help create the Obsidian vault.
  - I will help create a mission-control layer that can answer from wiki, Obsidian, and raw data when requested.
- Delivery target discussed: by Monday.
- Transcript tooling:
  - `kb/scripts/fetch_transcripts.py` fetches Supadata transcripts from any input file containing YouTube URLs or video IDs.
  - Raw transcript files are stored as `kb/sources/raw/<videoID>.md`.
  - Existing raw transcript files are skipped by default so runs are resumable.
  - All 35 playlist videos were fetched successfully on 2026-06-30 with 0 failures.
- WikiLLM:
  - `docs/sfs-wikillm.md` is the concrete AI operating prompt for the Startup for Startup wiki layer.
  - First product implementation lives under `kb/wikillm/` by David's request.
  - Initial pilot processed 3 episodes and established the structure for episode pages, concept pages, people pages, playbooks, claims, and questions.
  - Full-corpus draft was generated on 2026-06-30 across all 35 playlist episodes.
  - The full draft has 91 wiki markdown files, 35 episode pages, 440 timestamped source/evidence lines, and 0 missing internal wiki links in the final check.
  - `companies/Monday.com` should not be generated as a KB entity; original source titles/quotes that contain Monday/Monday.com can remain because they are source metadata.
  - Current next quality step: deep synthesis/linting of generated pages and concept/entity classification.
