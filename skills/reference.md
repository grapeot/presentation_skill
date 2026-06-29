# Presentation Skill — Reference

Detailed contracts and acceptance criteria. Read after the Quick Start in `skill_presentation.md`.

## When To Use

Use when the user asks an AI agent to create, redesign, or iterate on a presentation deck, slide narrative, speaker notes, or deck scaffold.

This skill is not a general image prompt skill, not a PowerPoint editing skill, and not a design review checklist. It owns the presentation workflow and deck acceptance criteria.

## Image-Generated Deck Contract

Produce before rendering:

- Deck-level thesis in one sentence
- Slide sequence where every slide advances one claim
- Visual direction: materials, lighting, color semantics, typography, layout rules, forbidden styles
- Per-slide prompts with exact readable text
- Asset references for logos, screenshots, charts, QR codes, or any pixel that must be exact

Put generated files under `generated_slides/` or `output/`. Do not copy API keys into prompts or docs.

### Acceptance criteria

- Each slide has a single claim understandable without speaker notes
- On-slide text is exact, legible, not decorative
- Visuals explain or structure the claim
- Style is consistent because prompts share one visual direction
- Asset-dependent slides use real source assets, not hallucinated logos or QR codes
- Deck has a preview path and speaker notes

## HTML Module Fallback Contract

Keep one logical slide per module. Each module exposes a predictable interface and keeps slide-specific state local.

### Acceptance criteria

- Deck opens from local `index.html` via `start-server.py` or equivalent static server
- Each slide has one main claim and enough visual structure
- Interactive slides clean up resources when leaving the slide
- Speaker notes present where spoken context is needed
- No undocumented global state

## Deck Quality Rules

Slides are dual-use: live talk and handout. A reader who missed the talk should recover the core argument from slides alone.

Speaker notes add context, transitions, examples, and emphasis — they do not read the slide back.

## Scaffold Layout

After `presentation-skill` init:

**Image mode (`--mode image`):**

```
deck_work/
  README.md              # operational guide (copied from bootstrap)
  deck_plan.md
  index.html             # Reveal.js + generated_slides backgrounds
  outline_visual.md
  visual_guideline.md
  generated_slides/
  tools/
  start-server.py
  css/  js/
  examples/html/         # full HTML module reference deck
```

**HTML mode (`--mode html`):**

```
deck_work/
  README.md
  deck_plan.md
  index.html             # Reveal.js + ES module loader
  js/slides/
  start-server.py
  css/  js/
  examples/image/        # full image-deck reference
```

## CLI Installation

```bash
uv venv .venv
uv pip install --python .venv/bin/python -e '.[dev]'
bash scripts/presentation-skill --help
```

## Installation Acceptance Criteria

The skill is installed when:

- Exactly one root skill from this repo is discoverable (`skills/skill_presentation.md`)
- `presentation-skill --help` works if the package is installed
- Offline tests pass during development
- Private credentials and local aliases stay outside the public repo

## Failure Handling

| Situation | Action |
|-----------|--------|
| Image generation unavailable | State blocker; keep source artifacts complete; ask for credentials or switch to HTML only if user allows |
| Garbled generated text | Simplify visible text, increase typographic emphasis, or textless background + HTML/CSS overlay |
| Visual drift across slides | Stop per-slide style variations; strengthen shared visual direction |

See also **Known traps** in `skill_presentation.md` for install-path confusion, silent mode downgrade, and paradigm mixing.
