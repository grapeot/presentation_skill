# Presentation Skill

Presentation Skill helps AI coding agents create slide decks. It defaults to image-generated decks, where each slide is rendered as a complete visual scene. HTML mode generates the deck as a web page: one borderless, animated canvas with a camera, written in HTML, CSS and SVG, where diagrams draw themselves, cards split and numbers roll on each click, with exact copy in the DOM, textless generated plates, and copy drafted by a writing model and fact-checked by the builder.

This repo is a public, platform-agnostic skill package. It works with agents such as OpenCode, Claude Code, Cursor, Codex, or any terminal coding agent that can read Markdown instructions and write files.

## Install Into An Agent Workspace

Give your agent this repository URL and ask it to install the skill:

```text
Install this public skill repo into my workspace:
https://github.com/grapeot/presentation_skill

Start from my workspace AGENTS.md or CLAUDE.md. Follow any WORKSPACE.md or skills/INDEX.md routing rules. Clone or vendor the repo under an appropriate project directory. Expose exactly one root skill to my global skill index or agent instructions. Keep private aliases, local paths, credentials, endpoint defaults, and business context in a local overlay, not in the public repo.
```

The root skill is `skills/skill_presentation.md`.

## Modes

Image-generated mode is the default. The agent creates a deck plan, a visual direction, slide prompts, local artifacts, and rendered images through the workspace's configured image generation tool.

HTML mode is a first-class alternative for talks, lectures, pitches and explainers that should move, and for decks that must keep exact copy, code, real data or links. See `skills/html_decks.md`. It was designed and validated with Claude Opus 5.5 as the builder; other models are untested (GPT-6 Astra is the suggested alternative). Rendering mode and asset policy are independent.

```bash
scripts/presentation-skill "Visual keynote" --mode image --output deck
scripts/presentation-skill "Technical briefing" --mode html --assets mixed --output deck
```

`--mode reveal` remains a compatibility alias for `html`.

## Local Development

```bash
uv venv .venv
uv pip install --python .venv/bin/python -e '.[dev]'
.venv/bin/python -m pytest -v
scripts/presentation-skill --help
```

The tests are offline and validate the planning contract, starter artifact generation, and installation contract.
