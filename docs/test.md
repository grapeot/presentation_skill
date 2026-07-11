# Test Strategy

## Overview

All default tests are **offline**: no API keys, no network, no browser automation. Image rendering belongs to the installing workspace; this repo validates contracts and scaffold generation only.

## Unit tests

Command:

```bash
uv venv .venv
uv pip install --python .venv/bin/python -e '.[dev]'  # dev extra includes img2pdf + pypdf for export tests
.venv/bin/python -m pytest -v
```

### `tests/test_deck_plan.py`

Covers `deck_plan.py`:

- `choose_mode()` defaults to image; explicit HTML phrases select html mode
- `validate_deck_plan()` catches empty plans, duplicate slide numbers, non-sequential numbering, missing titles, short claims/visual roles
- `build_deck_plan()` renders expected markdown and raises on invalid input

### `tests/test_cli.py`

Covers end-to-end CLI via `scripts/presentation-skill`:

- `--help` renders
- `--mode image` creates root image deck + `examples/html/` + `README.md`
- `--mode html` creates root HTML deck + `examples/image/` + sample JPEG fixture

### `tests/test_public_contract.py`

Covers repo invariants:

- Exactly one root skill file (`skill_presentation.md`); `reference.md` is supporting doc only
- Required docs exist (`prd.md`, `rfc.md`, `working.md`, `test.md`)
- No legacy large artifacts at repo root
- README points to root skill and public GitHub URL

## Integration tests

None in v1. Deck-level `tools/generate_slides.py` calls workspace image APIs; that path is validated manually in a scaffolded deck with real credentials outside CI.

## Manual validation before push

Checklist:

- [ ] `pytest -v` — all tests pass
- [ ] `bash scripts/presentation-skill "Smoke test" --mode image --output /tmp/deck_smoke`
- [ ] `cd /tmp/deck_smoke && uv venv .venv && uv pip install -r requirements.txt && .venv/bin/python start-server.py --port 8765 --no-browser` — preview loads
- [ ] `.env.example` contains fake placeholders only
- [ ] Privacy scan: `rg -n "op://|sk-[a-zA-Z0-9]{10,}|/Users/" .` returns no matches in tracked files

## What "done" means for a scaffolded deck (agent-facing)

This is not automated in CI but defines manual acceptance for deck work:

1. `deck_plan.md` lists one claim per slide
2. Active mode artifacts exist and preview via `start-server.py`
3. `speaker_notes.md` present
4. Agent left a validation note describing what was checked

## Future test ideas (not implemented)

- Opt-in live test for `generate_slides.py` behind `PRESENTATION_SKILL_LIVE_TESTS=1`
- CLI `--validate-deck-plan` parsing markdown into `SlideSpec` list
- Playwright smoke on example `index.html` (optional; user may skip if preview confirmed manually)


### `tests/test_export_pdf.py`

Covers `export_pdf.py` and the `export-pdf` CLI subcommand, fully offline (synthetic decks with pure-Python-generated PNGs):

- compatibility gate passes on background+notes-only sections and counts hotzones
- gate rejects: extra visible content in a section, missing background files, invalid overlay rects, non-http(s) hrefs, overlay ids with no matching section
- `export_pdf()` writes a PDF with one page per section and `/Link` annotations whose `/Rect` matches the fractional coords + default padding (y-flipped to PDF space)
- decks without an overlay block export with zero annotations
- CLI: `--check-only` exit codes (0 compatible / 2 incompatible), full export path, and the legacy positional `init` invocation still scaffolding
