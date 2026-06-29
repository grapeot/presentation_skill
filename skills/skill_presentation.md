---
name: presentation
description: >-
  Creates presentation slide decks for AI agents. Defaults to image-generated
  full-slide visuals (outline_visual.md, visual_guideline.md, Reveal.js viewer).
  Falls back to HTML/JS module decks when the user requests no image generation,
  editable HTML, or interactive slides. Use for slide decks, keynotes, teaching
  decks, speaker notes, or presentation scaffolds.
---

# Presentation Skill

## Quick Start

```bash
# From the presentation_skill repo (or after pip install -e .)
bash scripts/presentation-skill "Quarterly product strategy" --mode image --output deck_work
bash scripts/presentation-skill "Interactive demo" --request "HTML only" --output deck_work
```

Then preview:

```bash
cd deck_work
uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python start-server.py --port 8765 --no-browser
# Open http://localhost:8765
```

## Mode Selection

| Mode | When | Active files at deck root |
|------|------|---------------------------|
| **image** (default) | Keynote, executive, teaching, narrative decks | `outline_visual.md`, `visual_guideline.md`, `generated_slides/`, `tools/`, image `index.html` |
| **html** | User says "no image generation", "HTML only", "editable HTML", "interactive deck" | `index.html`, `js/slides/*.js`, `js/slideModule.js` |

Both modes copy a **reference example of the other mode** under `examples/` for cross-learning.

## Agent Workflow Checklist

```
- [ ] Run presentation-skill CLI to scaffold deck_work/
- [ ] Read deck_work/README.md and deck_plan.md
- [ ] Read the active-mode reference (root files) AND skim examples/<other-mode>/
- [ ] Write slide plan: one claim per slide, exact on-slide text
- [ ] Build content (image: outline + guideline; html: js/slides modules)
- [ ] Preview with start-server.py and verify navigation
- [ ] Write speaker_notes.md and a validation note
```

## Image Mode (default)

1. Edit `visual_guideline.md` — shared materials, lighting, typography, forbidden styles.
2. Edit `outline_visual.md` — one `#### Slide N:` block per slide with exact text in prompts.
3. Put exact assets (logos, QR codes, screenshots) under `imgs/`; reference them in outline Asset sections.
4. Render: `python tools/generate_slides.py --outline outline_visual.md` (uses workspace image API keys via `.env`).
5. `index.html` displays slides via Reveal.js `data-background="generated_slides/slide_NN_0.jpg"`.
6. Speaker notes go in `<aside class="notes">` inside each `<section>`.

**Before editing:** read root `outline_visual.md`, `visual_guideline.md`, and `examples/html/` to know when HTML modules are a better fit.

## HTML Module Mode

1. One slide per file under `js/slides/` (see `examples/html/js/slides/title.js`).
2. Each module exports `render(container)`, `initialize()`, `cleanup()` via the contract in `js/slideModule.js`.
3. Register IDs in `index.html`: empty `<section id="slideN">` plus the `slideIds` array.
4. Interactive slides must clean up timers, listeners, charts, and WebGL in `cleanup()`.

**Before editing:** read root `js/slides/` and `examples/image/` to understand the image-generation alternative.

## Core Deliverables

Every completed deck directory must include:

- `deck_plan.md` — audience, thesis, slide list, mode
- `visual_guideline.md` (image) or module notes (html)
- Per-slide source with exact on-slide text and visual role
- Previewable output (`index.html` + assets)
- `speaker_notes.md`
- Validation note (what was checked, what remains)

## Quality & Failure Rules

- One claim per slide; concrete text beats topic labels like "Architecture".
- Do not ask the image model to invent text — specify exact readable copy.
- Do not silently downgrade to HTML when image generation fails; state the blocker.
- If generated text is garbled, simplify copy or overlay exact text in HTML/CSS.
- Prefer the workspace `image-generation-skill` when available.

## Additional Resources

- Acceptance criteria, contracts, and installation notes: [reference.md](reference.md)
- Example decks ship in every scaffold under root (active mode) and `examples/` (reference mode)
