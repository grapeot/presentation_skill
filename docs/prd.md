# PRD: Presentation Skill

## Goal

Create a public AI-agent skill for producing presentation decks. The skill defaults to image-generated decks and falls back to HTML module decks when the user explicitly asks not to use image generation.

## Users

- AI coding agents installing public skills into a workspace.
- Humans who want an agent to make keynote, teaching, product, or technical presentation decks.
- Future maintainers consolidating legacy `nbp_slides` and `cursor_slides` workflows.

## Requirements

- Expose exactly one root skill file.
- Keep the public repo free of private paths, credentials, generated artifacts, large PDFs, and visual style libraries copied from legacy repos.
- Define mode selection clearly: image generation by default, HTML fallback only on explicit request or hard technical need.
- Provide offline tests that validate the planning contract and starter helper.
- Use English as the project working language.

## Non-Goals

- Shipping a full image-generation implementation.
- Shipping the old visual style catalog.
- Shipping old generated decks, PDFs, or large binary assets.
- Replacing dedicated PPTX editing tools.

## Success Criteria

- A fresh agent can install and discover the root skill.
- The root skill gives enough acceptance criteria for an agent to know when a deck is complete.
- Offline tests pass without API keys.
- Privacy scan finds no real credentials or private workspace references.
