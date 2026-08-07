# OKF Operating Model for David and Chloe

## Purpose

This document turns Open Knowledge Format (OKF) into a working model for how David and Chloe capture, structure, correct, retrieve, and reuse knowledge.

The goal is simple:
- keep capture lightweight
- keep knowledge structured
- keep decisions durable
- keep retrieval fast
- keep correction easy
- keep the system small enough to actually use

## Core Principle

Treat knowledge as an asset with a lifecycle.

That means every item should move through a small number of clear states:
- raw
- processed
- durable
- retrievable
- correctable

If a piece of information does not fit one of those states, it probably does not belong in the system yet.

## Working Assumptions

- David prefers short, high-signal interactions.
- WhatsApp is the main capture surface.
- A capture-only message must be preserved literally.
- Durable decisions belong in files, not only in chat.
- Chloe should classify and route, not over-explain.
- NotebookLM is a thinking and retrieval layer, not the source of truth.

## The OKF Loop

The working loop is:
1. Capture
2. Classify
3. Validate
4. Link
5. Store
6. Retrieve
7. Correct
8. Distill

### 1. Capture

- David sends raw input.
- If the message is capture-only, the exact text is preserved.
- No reinterpretation happens at this stage unless a rule explicitly requires it.

### 2. Classify

Chloe decides whether the item is:
- a task
- a decision
- a fact
- a question
- a reference
- a project note
- something to archive

Classification should be quick and practical.
If the category is unclear, ask one short question only when necessary.

### 3. Validate

Before something becomes durable:
- check if it is accurate
- check if it duplicates existing knowledge
- check if it contradicts an earlier decision
- check if it belongs in memory or only in a daily log

Validation is not about perfection.
It is about avoiding avoidable mistakes.

### 4. Link

Connect the item to related material.

Good links are:
- a related project
- an earlier decision
- a recurring person or topic
- a source document
- a memory note

Keep linking simple.
Do not over-engineer a graph.

### 5. Store

Store the item in the right place:
- raw logs for original inputs
- working notes for processed material
- durable files for long-lived decisions
- memory for important patterns and lessons

Never overwrite raw input.
Version instead of replacing when possible.

### 6. Retrieve

Retrieval should answer one question:
Can we find the right thing quickly when we need it?

Use the simplest possible path:
- search files first
- use memory for long-lived context
- use NotebookLM for cross-source synthesis

### 7. Correct

If something is wrong:
- correct the durable record
- keep the old version only if it has value
- note why the correction happened

Corrections should be easy and visible.

### 8. Distill

Regularly move useful patterns from daily logs into long-term memory.

Only keep what matters:
- recurring preferences
- stable decisions
- repeated lessons
- important rules

Do not promote noise into memory.

## What David Should Do

- Send raw input without trying to format it perfectly.
- Use capture-only messages for literal intake.
- Keep questions short.
- Trust the system to sort later.
- Give feedback when a classification is wrong.

## What Chloe Should Do

- Classify quickly.
- Ask one short question only when needed.
- Preserve literal capture exactly when required.
- Write durable decisions to files.
- Keep memory clean and selective.
- Avoid turning every item into a project.

## What to Avoid

- turning chat into the only record
- over-linking everything
- writing long explanations when a short decision would do
- creating new file structures for every new idea
- promoting raw noise into memory

## Recommended Minimum Standard

Every item should answer these questions:
- What is it?
- Where does it belong?
- Is it durable?
- Is it linked?
- Is it retrievable?
- Does it need correction later?

If the answer is unclear, simplify the item rather than adding complexity.

## Success Criteria

The system is working if:
- David can capture quickly
- Chloe can classify without friction
- important decisions are durable
- NotebookLM can find and synthesize relevant context
- old mistakes can be corrected
- the workflow stays light enough to use every day

