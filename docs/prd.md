# PRD: Presentation Skill

## Goal

Ship a public AI-agent skill for creating presentation slide decks. Default mode renders each slide as a cohesive full-slide image; fallback mode builds editable Reveal.js HTML/JS module decks when the user explicitly avoids image generation.

## Users

- AI coding agents installing public skills into a workspace (Codex, Claude Code, Cursor, OpenCode, etc.).
- Humans who want an agent to produce keynote, teaching, product, or technical decks with speaker notes.
- Maintainers consolidating legacy `nbp_slides` and `cursor_slides` workflows into one package.

## Problem

Agents lack a single, opinionated contract for presentation decks. Legacy repos split image generation and HTML module workflows; neither exposed a discoverable skill with preview path, examples, and acceptance criteria.

## Requirements

### Skill & docs

- Expose exactly one root skill: `skills/skill_presentation.md`.
- Use progressive disclosure: operational quick-start in the root skill, detailed contracts in `skills/reference.md`.
- Keep `docs/prd.md`, `docs/rfc.md`, `docs/working.md`, and `docs/test.md` current per workspace project-scaffold standards.

### Modes

- **Image mode (default)**: agent edits `outline_visual.md` + `visual_guideline.md`, renders via workspace image tooling, previews through Reveal.js `index.html` with `data-background` images.
- **HTML mode (fallback)**: agent edits `js/slides/*.js` modules; triggered only by explicit user phrases such as "HTML only" or "no image generation".

### CLI scaffold

- `presentation-skill` copies templates to a target directory.
- Active mode lands at deck root; the other mode lands under `examples/` for cross-reference.
- Every scaffold includes `README.md` with preview and generation steps.

### Public safety

- No real credentials, private paths, or personal data in the public repo.
- `.env.example` uses fake placeholders only.
- Example slide JPEGs are committed as offline preview fixtures (small set, no legacy PDF/catalog).

### Offline helpers

- Small Python package under `src/presentation_skill/` for mode selection, deck-plan validation contract, and starter generation.
- No direct image API calls from this repo.

## Non-Goals

- Shipping a full image-generation implementation (belongs to installing workspace).
- Shipping the old visual style catalog or large binary artifacts.
- PPTX editing, design review checklists, or live browser E2E in CI.

## Success Criteria

- A fresh agent can install the skill, run the CLI, preview a deck with `start-server.py`, and know when a deck is complete.
- Offline tests pass without API keys (`pytest -v`, currently 16 tests).
- Privacy scan finds no real credentials or private workspace references.
- PR #2 merges with consolidated templates and updated skill docs.

## Out of Scope (v1)

- CLI validation of agent-written `deck_plan.md` files (contract exists in tests; wiring deferred).
- Live image-generation integration tests.
