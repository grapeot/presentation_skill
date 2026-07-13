# Working Notes

## Changelog

### 2026-07-12

- Added `skills/speaker_notes.md` as progressive-disclosure guidance for authoritative, conversational direct-read scripts.
- Added measurable delivery gates: one main payload per sentence, breath-test review above 24 words, concept-before-term, cross-slide handoff ledger, and separate spoken/demo timing.
- Documented real failure modes from long-deck revisions: textbook delivery, decorative idioms, repeated transition questions, nested three-part sentences, factual drift, and batch-boundary breaks.
- Linked the new guidance from the root presentation skill while preserving exactly one discoverable root skill.
- Updated the public-contract test to distinguish the one frontmatter-bearing root skill from supporting Markdown resources.
- Verified `.venv/bin/python -m pytest -v` — 25 tests passed. Privacy scan of `skills/*.md` found no private paths, credentials, or deck-specific names.

### 2026-07-10

- Added `export-pdf` CLI subcommand: image-deck → distribution PDF with clickable link annotations, built straight from slide images (img2pdf lossless) + overlay-data rects (pypdf `/Link` annots, same 1.5% pad as the HTML layer). No browser printing.
- Compatibility gate (`--check-only`): every section must be background-image + notes only, backgrounds must exist, overlay JSON must be sane — otherwise fail loudly per section; never emit a lossy PDF silently.
- CLI moved to subcommands (`init`, `export-pdf`); legacy positional invocation auto-routes to `init` so existing scripts keep working.
- New optional dependency group `[pdf]` (img2pdf, pypdf); `[dev]` includes them for tests.
- Added `tests/test_export_pdf.py` (9 tests, offline, synthetic PNG decks). Verified `.venv/bin/python -m pytest -q` — 25 tests passed.
- Dogfooded on a real 25-slide / 15-hotzone production deck: check passed, PDF verified page count, link count, and URI targets.

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
