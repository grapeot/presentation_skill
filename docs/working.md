# Working Notes

## Changelog

### 2026-09-11

- Upgraded the OpenAI image backend from `gpt-image-2` to the GPT Image 2.5 family. Two variants at the same price: `gpt-image-2.5-flare` (speed-first) and `gpt-image-2.5-sunburst` (precision-first). Variant defaults to size (`1K -> flare`, `2K/4K -> sunburst`) with a `--variant auto|flare|sunburst` override.
- Changed the default quality tier from `low` to `auto`, and expanded `--quality` to `low|medium|high|xhigh|max|auto` (2.5 adds `xhigh`/`max`). 2.5's quality scale is finer: 2.5 `high` costs roughly a quarter of GPT Image 2 `high`, and 2.5 `max` matches the old `high` spend.
- Removed the multi-asset Pillow stacking workaround: GPT Image 2.5 accepts multiple input images in one `images.edit` call, so `generate_slides.py` now passes every `Asset` path straight through. Updated `skills/skill_presentation.md` and `skills/reference.md` to document the two variants, the size mapping, and native multi-image input.
- Added `tests/test_generate_slides.py` (7 offline tests) covering variant resolution and overrides, parser defaults, the expanded quality tiers, `auto` default, size→variant flow, and multi-asset pass-through with no stacking.
- Updated `docs/prd.md` (image-backend requirements + test count), `docs/rfc.md` (image backend decision record), and `docs/test.md` (new test module).
- Verified offline test suite (`.venv/bin/python -m pytest -q`, 47 passed) and validated variant resolution, parser defaults, and model-id pass-through with a stubbed harness; the template tools require the deck's own runtime deps and are not imported by the package.

### 2026-07-18

- Reframed HTML fallback as first-class Reveal mode and separated rendering mode from local asset policy (`none`, `generated`, `exact`, `mixed`).
- Kept `--mode html` and `write_html_mode_starter()` as compatibility aliases while new plans emit `Mode: reveal`.
- Replaced the legacy all-modules HTML example with a static deck registry plus one lifecycle-managed interactive module.
- Added a public-safe transparent CPU blueprint fixture and card-visual example inspired by a production teaching deck without copying its course content.
- Added `skills/reveal_decks.md` and `skills/generated_assets.md` as progressive-disclosure contracts.
- Added provider-neutral `prepare-asset` alpha extraction, tint, and crop tooling with offline Pillow tests.
- Verified `.venv/bin/python -m pytest -v` (40 passed), checked both new JavaScript modules with `node --check`, and found no private paths or live credentials beyond documented fake `.env.example` placeholders.

### 2026-07-16

- Added a podium test to the speaker-notes contract: every paragraph must sound natural when addressed to a room, not merely read well in a memo.
- Added guidance to translate audit and authoring abstractions into observable actions and direct checks, with an explicit trap for audit-report voice.
- Added slide-role fidelity: notes must derive from the locked visible claim, visual role, and chapter handoff rather than from a merely plausible narrative.
- Separated mechanism, demo, and management-move responsibilities; management moves now extract the underlying human-management principle instead of repeating the preceding AI mechanism.
- Added artifact-state fidelity for demo narration and grounded expansion rules for longer talks.
- Added spoken logical signposting for a non-rewind medium: cue continuation, consequence, contrast, limitation, and handoff before introducing the next payload, while avoiding repetitive transition wallpaper.
- Tightened the breath test into a hard gate: ordinary spoken sentences must stay at or below 22 words and carry no more than one main payload plus one supporting clause.

### 2026-07-14

- Extended image-deck overlays and PDF export to accept safe relative local links alongside HTTP(S) URLs.
- Kept absolute filesystem paths and executable URI schemes rejected; added compatibility and PDF target-preservation tests.
- This allows a deck and a PDF placed beside its `index.html` to share measured hotzones for local handouts and demo artifacts.

### 2026-07-12

- Added `skills/speaker_notes.md` as progressive-disclosure guidance for authoritative, conversational direct-read scripts.
- Generalized the speaker-notes introduction gate: motivation must precede structure. New concepts, frameworks, and lists now require a clear `why now`; lists may compress established understanding but cannot create it. Added why-now, handoff, and time ledgers plus traps for summary-as-introduction and list-without-parent-question failures.
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


## 2026-09-28 — Reveal mode becomes the courseware canvas (breaking)

- Replaced the per-slide DOM-card Reveal scaffold with a canvas engine: one world sheet, frames auto-laid-out in slide order, slides addressed by id, state as a pure function of (slide, step), camera moves, motion vocabulary (pen, plate ink-in, type-on, counters, split-flap, split cards).
- New scaffold tooling: `tools/build_index.py`, `tools/copy_to_js.py`, `tools/shoot.py` (every step, contact sheets, offline/error report), `tools/vendor.mjs`; writer packet templates under `copy/`.
- New skill docs: `copy_workflow.md` (writer drafts, builder checks), `critic_review.md`; `reveal_decks.md` rewritten; plates section in `generated_assets.md`; model note (designed for Claude Opus 5.5).
- `examples/html/` renamed to `examples/reveal/`; `js/slides/` modules and `slideModule.js` are gone from the reveal scaffold (live content uses `DECK_HOOKS`).
- Lessons come from a real 40-slide, ~51-minute guest lecture built with this workflow (traps table in `reveal_decks.md`).
- Validation: offline pytest suite; scaffolded a reveal deck from the CLI, vendored it, and ran `tools/shoot.py`.

## 2026-09-28 — HTML is the mode name; the canvas is not only for courseware

- Canonical mode is `html` again (`DeckMode.HTML`, `write_html_mode_starter`, `Mode: html`); `reveal` stays as a compatibility alias in the CLI, enum and starter. Reveal.js is described as plumbing (navigation, notes, speaker view), not the mode.
- `examples/reveal/` → `examples/html/`; `skills/reveal_decks.md` → `skills/html_decks.md`.
- Dropped "courseware" framing: the canvas is a borderless animated sheet for keynotes, lectures, pitches, walkthroughs and explainers. Template chrome reads "Event · Talk title".
- Added an SVG section to `html_decks.md`: structure (diagrams, charts, connectors) is hand-written inline SVG in the deck's register; plates carry material.

## 2026-09-28 — PDF export for HTML (canvas) decks

- `export-pdf` now exports HTML (canvas) decks through headless Chromium (`src/presentation_skill/export_html_pdf.py`). It picks this path when the deck has `js/engine.js` and `window.DECK`; `--mode image|html` overrides. The image-deck path is unchanged.
- One page per slide at its print state: the last step by default, or `print: <step>` on the slide entry. The template's `S()` helper takes an optional fifth `opts` argument for it. During export `<html>` carries `pdf-export` and `data-print-slide` / `data-print-step`, so a deck can write a dedicated handout layout in CSS.
- Rendering: private loopback server on a free port, 1920×1080 viewport, screen media, transitions and CSS animations off, `deckGoto(i, step)`, wait until the DOM stops changing, then `page.pdf` at 1920×1080 with backgrounds and `page_ranges="1"`. Pages are merged with pypdf. A content-hash dedupe then stores repeated images once (Chromium emits a separate copy per page).
- `--with-notes` adds a full notes page after each slide (from `COPY[id].notes`, else the Reveal notes aside), in the deck's body font and paper colour, two columns, auto-sized 30→16 px.
- The export fails loudly on page-count mismatch, console or page errors, failed local requests, any non-loopback request (aborted and reported), `.missing` slots, fonts with status `error`, bad `print` values, or pages that are not one 1440×810 pt page. It writes `<name>_contact_NN.jpg` next to the PDF (pymupdf or pdftoppm).
- New optional extra `[pdf-html]` (playwright, pypdf, Pillow). A missing Playwright or Chromium gives an install hint and exit code 3.
- Tests: `tests/test_export_html_pdf.py`. The unit tests need no browser. The browser tests export the template deck with a stub Reveal, and skip when Playwright/Chromium is missing. `.venv/bin/python -m pytest -q`: 86 passed locally with Chromium; with Playwright hidden, the 5 browser tests skip.
- Real-world check on a 40-slide production canvas deck (its own engine copy and CSS, vendored Reveal and fonts): 40 pages (80 with notes), no warnings, about 17 s / 20 s. Every PDF page matched a screenshot of the same state taken after its transitions settled naturally (at most 0.3% of pixels differ, all antialiasing). The fonts are the deck's own (the variable fonts embed as Type 3 outlines, and text stays extractable). About 18 MB, almost all of it the deck's engraving plates.

Known limitations:

- A slide printed at `print: <step>` shows exactly that state; there is no automatic "union of all states" layout. Slides that hide information in every state need a handout rule in CSS.
- An infinite CSS idle animation prints at its first frame. JavaScript-driven motion that never settles is printed after 4 s, with a warning.
- Letters split into per-character spans (the `.type` effect) extract without word spaces in some PDF readers (pypdf); pymupdf reads the spaces correctly.
- Glyphs missing from a subsetted web font fall back to a system font, exactly as on screen (seen for "→" in a Latin-only mono subset).
