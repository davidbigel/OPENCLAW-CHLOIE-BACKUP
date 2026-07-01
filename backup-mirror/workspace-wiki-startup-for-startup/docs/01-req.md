# Requirements - Startup for Startup WikiLLM + Obsidian

## Project

Build a Hebrew knowledge system for the `startup for startup` channel.

The system will combine:

- a WikiLLM built from channel source material
- an Obsidian vault for structured knowledge work
- a mission-control interface for answering questions from the wiki, the vault, and raw data

## Owner

- Name: David
- Role: startup researcher in Israel
- Focus: med
- Workplace: Swiss embassy

## Agent

- Name: Snoracle
- Role: project agent responsible for building and documenting the system

## Goal

By Monday, have the core system direction, source-ingestion workflow, wiki generation path, Obsidian structure, and mission-control plan in place.

## Product Requirements

- Primary language: Hebrew
- Domain: startup insights
- Sources: YouTube playlist content from `startup for startup`
- Retrieval layers:
  - WikiLLM knowledge layer
  - Obsidian vault knowledge layer
  - raw transcript/source-data access when explicitly requested

## Planned Phases

### Phase 1 - Transcript ingestion

- David will create a Supadata API key
- David will provide the relevant YouTube playlist
- Snoracle will transcribe the latest 50 videos from that playlist

### Phase 2 - WikiLLM generation

- David will provide the prompt for creating the WikiLLM
- Snoracle will use the prompt and transcript corpus to create the WikiLLM

### Phase 3 - Obsidian vault

- David will define or refine the vault expectations
- Snoracle will help create the Obsidian vault structure and content workflow

### Phase 4 - Mission control

- Snoracle will help create a mission-control layer
- Users will be able to ask questions
- Answers should come from:
  - the wiki
  - the Obsidian vault
  - raw data, when the user explicitly asks for it

## Notes

- This document captures the initial user requirements only.
- Implementation details, architecture, folder structure, and prompt design will be refined in follow-up docs.
