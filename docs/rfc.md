# RFC: Consolidating Legacy Presentation Workflows

## Context

Two older repositories cover related presentation workflows:

- `nbp_slides`: image-generated full-slide deck workflow with generators and a style library.
- `cursor_slides`: HTML/JavaScript module deck scaffold optimized for Cursor-era agent workflows.

They share the same product space: helping agents create presentation decks. The new public skill keeps the reusable workflow contract and drops large or legacy artifacts.

## Decision

Create `presentation_skill` as a pure public skill repo with one root skill. The repo includes only offline helpers, docs, tests, and starter templates. It does not vendor the old PDF, generated examples, or visual style catalog.

Image-generated decks are the default because they produce coherent visual language with less manual layout work. HTML module decks remain a fallback for explicit no-image-generation requests, live demos, and editable web decks.

## Architecture

- `skills/skill_presentation.md`: root skill and workflow contract.
- `src/presentation_skill/`: offline helper library for mode selection, deck-plan validation, and starter artifact generation.
- `scripts/presentation-skill`: thin wrapper for the console command.
- `tests/`: offline contract tests.
- `docs/`: PRD, RFC, test strategy, working log, and privacy review.

## Integration Plan

- Install locally under `adhoc_jobs/presentation_skill` and expose one pointer in the workspace skill index.
- Add the public repo to `context-infrastructure/docs/SKILL_ECOSYSTEM.md`.
- Remove the older built-in `workflow_presentation_slides.md` from public `context-infrastructure` to avoid duplicated guidance.
- Add `presentation_skill` to the public `skills` registry.
- Mark `nbp_slides` and `cursor_slides` as deprecated with README PRs that point to this repo.
