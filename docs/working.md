# Working Notes

## Changelog

### 2026-06-27

- Created the public-ready `presentation_skill` scaffold with one root skill, offline helper library, docs, tests, and public-safety defaults.
- Consolidated the intended positioning of legacy `nbp_slides` and `cursor_slides` into image-generated default mode plus HTML fallback mode.
- Kept privacy review as a pre-push operating check rather than a public documentation artifact.
- Verified `.venv/bin/python -m pytest -v` passed 15 offline tests.
- Verified `scripts/presentation-skill --help` renders the CLI contract without manually activating the virtual environment.
- Ran a pre-push privacy scan for local workspace paths, private 1Password refs, common API key patterns, private keys, and email addresses; no matches found.

## Lessons Learned

- Keep this repo as a pure skill contract and small offline helper. Large style catalogs, generated decks, and PDFs belong outside the public skill package.
- Defaulting to image-generated decks should be a mode-selection rule, not a hard dependency on any specific provider or API key.
