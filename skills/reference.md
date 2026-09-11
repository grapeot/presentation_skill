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

### Multiple reference assets with GPT Image 2.5

GPT Image 2.5 accepts **multiple** input images in one call, so slides can reference several exact pixels — a navbar style sheet, a logo, and a QR code on the same closing slide — without preprocessing.

**Generator behavior:** When an outline slide lists multiple paths under `Asset`, `tools/generate_slides.py` passes them all to `client.images.edit` in list order. No stacking or compositing is performed.

**Outline + prompt contract:**

1. List every required asset under `Asset`, in the order they should be considered.
2. In the slide **提示词**, name each asset and its slide placement — e.g. 「导航条贴顶左对齐，Logo 居中于标题区上方，二维码嵌入右侧卡片」.
3. Do not omit reference assets; the model can use all of them in one call.

**Model variants and quality:**

- `gpt-image-2.5-flare` — speed-first; default at 1K.
- `gpt-image-2.5-sunburst` — precision-first; default at 2K/4K.
- Override the variant with `--variant flare|sunburst` (`auto` follows size). Quality defaults to `auto`; pin it with `--quality low|medium|high|xhigh|max|auto`. The 2.5 quality scale is finer than GPT Image 2's: 2.5 `high` costs roughly a quarter of GPT Image 2 `high`, and 2.5 `max` matches the old `high` spend.

**Draft vs final renders:** Use `--output-dir generated_slides_4k` (or similar) for final-quality batches; point `index.html` `data-background` at the chosen directory.

**Example Asset block (closing slide):**

```
*   **Asset**：
    - data/navbar_flow2_ref.png
    - data/superlinear_logo.png
    - data/superlinear_qr.png
```

### Acceptance criteria

- Each slide has a single claim understandable without speaker notes
- On-slide text is exact, legible, not decorative
- Visuals explain or structure the claim
- Style is consistent because prompts share one visual direction
- Asset-dependent slides use real source assets, not hallucinated logos or QR codes
- Deck has a preview path and speaker notes

## Reveal Deck Contract

Reveal mode keeps exact content and layout in the DOM while allowing generated icons and diagrams as local assets. Read [reveal_decks.md](reveal_decks.md) and [generated_assets.md](generated_assets.md) for the full contracts.

### Acceptance criteria

- Deck opens from local `index.html` via `start-server.py` or equivalent static server
- Each slide has one main claim and enough visual structure
- Static slides may share a deck registry; interactive slides clean up resources when leaving the slide
- Required copy and quantitative truth never depend on generated pixels
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
  examples/html/         # Reveal reference; legacy physical directory name
```

**Reveal mode (`--mode reveal`; `html` remains a compatibility alias):**

```
deck_work/
  README.md
  deck_plan.md
  index.html             # Reveal.js + ES module loader
  js/deck.js            # static slide registry
  js/slides/            # interactive modules only
  imgs/
  visual_guideline.md
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
| Image generation unavailable | State blocker; keep source artifacts complete; ask for credentials or switch composition to Reveal only if user allows |
| Garbled generated text | Simplify visible text, increase typographic emphasis, or textless background + HTML/CSS overlay |
| Visual drift across slides | Stop per-slide style variations; strengthen shared visual direction |

See also **Known traps** in `skill_presentation.md` for install-path confusion, silent mode downgrade, and paradigm mixing.
