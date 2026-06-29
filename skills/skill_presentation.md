# Presentation Skill

## When To Use

Use this skill when the user asks an AI agent to create, redesign, or iterate on a presentation deck, slide narrative, speaker notes, or deck scaffold.

Default to an image-generated deck: each slide is rendered as a cohesive full-slide visual, with readable text, diagrams, and visual hierarchy generated together. Use HTML module mode only when the user explicitly asks to avoid image generation, needs interactive/live elements, or requires editable HTML/CSS/JavaScript slides.

This skill is not a general image prompt skill, not a PowerPoint file editing skill, and not a design review checklist. It can call those capabilities if the installing workspace has them, but this skill owns the presentation workflow and deck acceptance criteria.

## Core Outcome

A completed deck directory must contain enough source material for another agent to continue the work without guessing:

- `deck_plan.md`: audience, thesis, narrative sequence, slide list, and mode.
- `visual_direction.md` for image mode, or `html_system.md` / module notes for HTML mode.
- Per-slide source: exact on-slide text, visual role, assets, and speaker-note intent.
- Rendered or previewable output: generated slide images plus a viewer for image mode, or an HTML deck for fallback mode.
- `speaker_notes.md`: notes that support the slide rather than repeat it.
- A validation note describing what was checked and what remains unresolved.

## Mode Selection

Choose image mode unless the user clearly says otherwise. Phrases such as "no image generation", "HTML only", "editable HTML", "interactive deck", or "do not render images" select HTML mode.

Image mode is best for keynote-style, executive, teaching, and narrative decks where visual unity matters. HTML mode is best for live demos, charts that must update in-browser, source-editable slides, or low-cost drafts when image generation is unavailable.

## Image-Generated Deck Contract

The agent should produce these artifacts before rendering:

- A deck-level thesis in one sentence.
- A slide sequence where every slide advances one claim.
- A visual direction that defines materials, lighting, color semantics, typography, layout rules, and forbidden styles.
- Per-slide prompts with exact readable text. Do not ask the image model to invent text.
- Asset references for logos, screenshots, charts, QR codes, or any pixel that must be exact.

Use the installing workspace's image generation tool. If the workspace has `image-generation-skill`, prefer that for rendering and upscaling. Do not copy API keys into prompts or docs. Put generated files under ignored output directories such as `generated_slides/` or `output/`.

Acceptance criteria for image mode:

- Each slide has a single claim that a reader can understand without speaker notes.
- On-slide text is exact, legible, and not merely decorative.
- Visuals explain or structure the claim; they do not serve as generic decoration.
- Style is consistent across the deck because prompts share one visual direction.
- Asset-dependent slides use real source assets instead of asking the model to hallucinate logos, QR codes, tables, or screenshots.
- The deck has a preview path and speaker notes.

## HTML Module Fallback Contract

HTML mode creates a local web deck. Keep one logical slide per module or clearly separated section. Each slide module should expose a predictable interface and keep slide-specific state local.

Acceptance criteria for HTML mode:

- The deck opens from a local `index.html` or documented dev server.
- Each slide has one main claim and enough visual structure to support it.
- Interactive slides clean up timers, event listeners, charts, WebGL scenes, or other resources when leaving the slide.
- Speaker notes are present for slides that need spoken context.
- The deck avoids global state unless a shared controller is documented.

## Deck Quality Rules

Presentation slides are dual-use: they support a live talk and also work as a handout. A reader who did not attend the talk should be able to recover the core argument from the slides alone.

Prefer concrete claims over topic labels. A slide titled "Architecture" is weak unless the visible text says what matters about the architecture. Use diagrams, contrasts, timelines, or examples to reduce cognitive load.

Speaker notes should add context, transitions, examples, and emphasis. They should not simply read the slide back to the audience.

## Failure Handling

If image generation is unavailable, do not silently downgrade the deck. State that rendering is blocked, keep all source artifacts complete, and either ask for credentials/tooling or switch to HTML mode only if that matches the user's constraints.

If generated text is garbled, simplify the visible text, increase typographic emphasis, or render a textless background and overlay exact text in HTML/CSS. Do not accept illegible text as final.

If the deck starts drifting visually, stop adding per-slide style variations and strengthen the shared visual direction.

## Local Helper & Example Starter Pack

This repository includes an offline starter helper CLI tool that sets up the full presentation runtime and copies high-quality examples to act as starting points:

```bash
# Initialize a new presentation project with templates and examples
presentation-skill "Quarterly product strategy" --mode image --output deck_work
presentation-skill "Interactive system demo" --request "HTML only" --output deck_work
```

### ⚠️ IMPORTANT: Follow the Examples
When the CLI initializes the directory, it copies functional examples of the selected mode into the target folder:
- **For Image Mode**: It copies a set of 5 sample high-fidelity slides under `generated_slides/` (`slide_01_0.png` through `slide_05_0.png`) and pre-populates `outline_visual.md`, `visual_guideline.md`, and the generation tooling scripts under `tools/`.
- **For HTML Mode**: It copies a complete set of slide JS modules under `js/slides/` (`title.js`, `slide1.js` through `slide6.js`) and configures `index.html`.

**AI Agent Instruction**: Before modifying or creating new slides, you **must** read and review these copied example slides/assets to understand the visual structure, layout principles, and code contracts. Build or adapt your new slides directly on top of these examples to guarantee high design quality and execution predictability.

## Installation Acceptance Criteria

The skill is installed when exactly one root skill from this repo is discoverable by the workspace, `presentation-skill --help` works if the package is installed, offline tests pass if the repo is under active development, and private credentials or local aliases remain outside the public repo.

