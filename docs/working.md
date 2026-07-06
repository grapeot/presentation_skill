# Working Notes

## Changelog

### 2026-07-06

- Added image-deck guidance for text-heavy slides: keep title regions wide, require normal-width typography, and prevent image models from horizontally squeezing long text.
- Added a trap for internal prompt constraints leaking into visible slide copy.
- Verified `.venv/bin/python -m pytest -v` — 16 tests passed.
- Privacy scan found only existing public-safety documentation references; no new private paths, credentials, or deck-specific context.

### 2026-06-29 (later)

- Rewrote `skills/skill_presentation.md` per `skill_creator_skill.md`: result-oriented acceptance criteria, known traps from real misroutes, removed SOP checklist.
- Verified `.venv/bin/python -m pytest -v` — 16 tests passed.

### 2026-06-29

- Restructured templates: `examples/{image,html}/` + `bootstrap/DECK_README.md`; CLI copies active mode to root and other mode under `examples/`.
- Rewrote `skills/skill_presentation.md` with quick-start, preview steps, agent checklist; added `skills/reference.md` for progressive disclosure.
- Expanded `docs/prd.md`, `docs/rfc.md`, `docs/test.md` to match project-scaffold standards; documented `deck_plan.py` vs `starter.py` split (replaced misleading `planner.py` name).
- Added CLI tests for cross-mode `examples/` layout and bootstrap `README.md`.
- Verified `.venv/bin/python -m pytest -v` — 16 tests passed.
- Pushed to PR #2 (`feature/consolidate-workflows`); user confirmed preview works manually (Playwright skipped).

### 2026-06-27

- Created public-ready `presentation_skill` scaffold with one root skill, offline helper library, docs, tests, and public-safety defaults.
- Consolidated legacy `nbp_slides` and `cursor_slides` positioning into image default + HTML fallback.
- Verified initial offline test suite and privacy scan passed.

## Lessons Learned

- Keep this repo as a pure skill contract and small offline helper. Large style catalogs, generated decks, and PDFs belong outside the public skill package.
- Defaulting to image-generated decks is a mode-selection rule, not a hard dependency on any specific provider or API key.
- Do not name Python modules `planner` when they do not plan anything — `starter.py` (scaffold copy) and `deck_plan.py` (validation contract) are clearer.
- Canonical workspace path is `adhoc_jobs/presentation_skill/`, not `.agents/skills/` (stale Cursor injection can misroute agents).
- Example JPEGs in `templates/examples/image/generated_slides/` are intentional offline fixtures for preview; regenerate only when example content changes.

## Open Questions

- Wire `deck_plan.py` validation into CLI (`--validate-deck-plan`) if agents frequently ship thin deck plans.
- Add opt-in live test for `generate_slides.py` when CI secrets are available.
