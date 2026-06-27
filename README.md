# Presentation Skill

Presentation Skill helps AI coding agents create slide decks. It defaults to image-generated decks, where each slide is rendered as a complete visual scene. If the user explicitly asks to avoid image generation, it falls back to an HTML module deck inspired by SlidePilot and Reveal.js.

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

HTML module mode is a fallback. Use it when the user says not to use image generation, when the deck must be editable as HTML/CSS/JavaScript, or when the content requires live charts or interactive demos.

## Local Development

```bash
uv venv .venv
uv pip install --python .venv/bin/python -e '.[dev]'
.venv/bin/python -m pytest -v
scripts/presentation-skill --help
```

The tests are offline and validate the planning contract, starter artifact generation, and installation contract.
