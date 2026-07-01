# Startup for Startup Wiki App

This folder now contains a runnable local Python application for building an Obsidian-ready wiki from transcript files.

What it does:
- ingests local markdown and text transcript files
- normalizes transcript formatting
- chunks transcripts into stable segments
- builds episode and topic wiki pages
- exports an Obsidian-ready vault
- writes a JSON run report

Layout:
- src/startup_wiki/ - application code
- tests/ - unit tests and fixtures
- 05_obsidian_export/ - generated vault output
- 06_reports/run-report.json - pipeline report

CLI:
- build: run the full pipeline with input and workspace paths
- report: print an existing run report from the workspace
