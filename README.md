# Presentation Skill

Presentation Skill helps AI coding agents create slide decks. It defaults to image-generated decks, where each slide is rendered as a complete visual scene. Reveal mode keeps exact copy, layout, links, and interaction in HTML/CSS/JavaScript while optionally using generated icons and diagrams as local assets.

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

Reveal mode is a first-class alternative. Use it when the deck must preserve exact copy, remain editable, or include code, real data, links, fragments, or interaction. Rendering mode and asset policy are independent: `reveal` can use no generated images, generated local assets, exact assets, or a mix.

```bash
scripts/presentation-skill "Visual keynote" --mode image --output deck
scripts/presentation-skill "Technical briefing" --mode reveal --assets mixed --output deck
```

`--mode html` remains a compatibility alias for `reveal`.

## Local Development

```bash
uv venv .venv
uv pip install --python .venv/bin/python -e '.[dev]'
.venv/bin/python -m pytest -v
scripts/presentation-skill --help
```

The tests are offline and validate the planning contract, starter artifact generation, and installation contract.
