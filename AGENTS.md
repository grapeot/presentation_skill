# Presentation Skill

## What This Repo Is

This repository packages a public-safe presentation creation skill for AI coding agents. It exposes one root skill at `skills/skill_presentation.md` and a small offline helper library for validating deck plans and generating starter artifacts.

The skill unifies two presentation modes:

- Image-generated decks by default: the agent writes a deck plan, visual direction, and per-slide prompts, then uses the installing workspace's image generation capability to render full-slide images.
- HTML module decks as fallback: when the user explicitly asks not to use image generation, the agent creates a Reveal.js-style HTML deck with one module per slide.

## Working Environment

Use a project-local `.venv` created with `uv` when changing or testing the package.

```bash
uv venv .venv
uv pip install --python .venv/bin/python -e '.[dev]'
.venv/bin/python -m pytest -v
scripts/presentation-skill --help
```

The default test suite must stay offline. Do not add live image-generation tests unless they are explicitly opt-in through an environment variable and fake `.env.example` values.

## Code Boundaries

`src/presentation_skill/` contains only offline helpers:

- `starter.py` — CLI template copy and scaffold generation
- `deck_plan.py` — mode selection and deck-plan validation contract (testable spec, not an AI planner)

It must not call external image APIs directly. Image generation belongs to the installing workspace, commonly through an image-generation skill or another user-configured tool.

`skills/skill_presentation.md` is the only root skill exposed by this repo. `skills/reference.md` and `skills/speaker_notes.md` are progressive-disclosure support, not additional root skills.

## Public Safety

All docs, tests, and examples must use fake credentials, generic domains, and public-safe paths. Do not commit real API keys, private 1Password refs, local absolute workspace paths, generated decks, slide images, logs, or personal data.

Before handoff, run offline tests and a privacy scan. Record meaningful validation results in `docs/working.md`.
