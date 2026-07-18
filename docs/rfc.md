# RFC: Consolidating Legacy Presentation Workflows

## Context

Two older repositories cover related presentation workflows:

- `nbp_slides`: image-generated full-slide deck workflow with generators and a style library.
- `cursor_slides`: HTML/JavaScript module deck scaffold optimized for Cursor-era agent workflows.
- A production Reveal.js teaching deck proved generated icons can complement DOM composition without turning slides into full-slide images.

The new public skill keeps the reusable workflow contract and drops large or legacy artifacts.

## Decision

Create `presentation_skill` as a pure public skill repo with one root skill, offline helpers, docs, tests, and starter templates. Image-generated decks remain the default. Reveal decks are a first-class composition mode with an independent local asset policy.

Do not add a third hybrid mode. Rendering and assets answer different questions: `image` versus `reveal` selects the composition owner; `none`, `generated`, `exact`, or `mixed` selects the asset policy.

## Architecture

```
presentation_skill/
├── skills/
│   ├── skill_presentation.md   # root skill (quick-start + checklist)
│   └── reference.md            # detailed contracts (progressive disclosure)
├── docs/                       # prd, rfc, working, test
├── src/presentation_skill/
│   ├── deck_plan.py            # mode selection + deck-plan validation contract
│   ├── starter.py              # CLI template copy / scaffold generation
│   ├── export_pdf.py           # image-deck → clickable PDF (compat gate + img2pdf + link annots)
│   ├── cli.py                  # subcommands: init (legacy positional supported), export-pdf
│   └── templates/
│       ├── common/             # start-server.py, slideModule.js, css
│       ├── bootstrap/          # DECK_README.md → copied as deck README.md
│       └── examples/
│           ├── image/          # full image-deck reference
│           └── html/           # Reveal reference; legacy physical name retained
├── scripts/presentation-skill
└── tests/
```

## Scaffold Layout

CLI init copies the **active mode** to the deck root and the **other mode** under `examples/`:

| CLI flag | Deck root | Cross-reference |
|----------|-----------|-----------------|
| `--mode image` | image deck (`outline_visual.md`, `generated_slides/`, image `index.html`) | `examples/html/` |
| `--mode reveal` | Reveal deck (`js/deck.js`, optional modules, local assets) | `examples/image/` |

Both modes include `README.md` (from `bootstrap/DECK_README.md`) with preview and generation steps.

## Python helpers: what they are and why

The repo name `planner.py` (removed in favor of two modules) confused earlier reviewers. The Python code is **not** an AI planner. It is two small offline utilities:

### `starter.py` — essential

Used by the CLI. Copies template directories, writes stub `deck_plan.md`, copies bootstrap `README.md`. This is the mechanical scaffold agents need on day one.

### `deck_plan.py` — contract library, not runtime planner

Contains:

- `choose_mode()` — maps user request text to `image` vs `reveal` for `--mode auto`
- `choose_asset_policy()` — selects local asset policy independently from rendering mode
- `SlideSpec`, `validate_deck_plan()`, `build_deck_plan()` — encode the skill's deck-plan quality rules as testable Python

**Important:** the agent still writes `deck_plan.md` by hand (or via LLM). The Python functions do not call any model. They exist so:

1. Tests lock the contract ("one claim per slide", sequential numbering, minimum field length).
2. Future CLI flags (e.g. `--validate-deck-plan deck_plan.md`) can reuse the same logic without duplicating rules in Markdown.

If we never wire CLI validation, `deck_plan.py` still earns its keep as the executable spec behind the skill's acceptance criteria. Removing it would leave only prose with no machine-checkable contract.

### What we deliberately do not build

- No slide content generation in Python
- No image API calls
- No automatic outline → image pipeline (that lives in copied `tools/generate_slides.py` inside each deck scaffold, using workspace credentials)

### Reveal structure decision (2026-07)

Static slides default to one deck registry because most teaching slides contain markup but no state. Only slides with timers, listeners, charts, media, or WebGL use lifecycle modules. This keeps global editing cheap without weakening cleanup requirements where state actually exists.

Generated icons and diagrams are permitted inside Reveal slides. The DOM remains the composition owner and retains all exact text and data. `prepare-asset` supplies deterministic alpha extraction, tinting, and cropping; provider API calls remain outside this repo.

## Integration Plan

- Install locally under `adhoc_jobs/presentation_skill`; workspace pointer at `rules/skills/presentation_skill.md`.
- Add to public `skills` registry and deprecate `nbp_slides` / `cursor_slides` with README pointers.

## Migration Notes

Legacy repos may be referenced for historical examples. This repo vendors a trimmed example set under `templates/examples/` only.


## PDF Export Decision (2026-07)

Browser `?print-pdf` proved lossy for image decks: it rewrites overlay links to the visible pill text (404s) and mis-sizes pages unless Reveal is configured just so. Since a compatible image deck is fully described by (ordered background images, overlay-data JSON), the export path builds the PDF from those two inputs directly: `img2pdf` for lossless page embedding, `pypdf` for `/Link` annotations at the same fractional rects (+1.5% pad) the HTML overlay layer uses. The compatibility check is a hard gate, not a warning: a section carrying any visible content beyond background + notes fails the export, because that content would silently vanish from the PDF. Dependencies stay out of the core install as the `[pdf]` extra.
