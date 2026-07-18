# Reveal Deck Contract

Reveal mode uses the browser as the composition owner. Choose it when exact copy, editable structure, code, real data, links, fragments, or interaction matters more than holistic full-slide rendering.

## Acceptance criteria

- The DOM owns every word, number, link, and layout relationship that must be exact.
- A reader can recover one concrete claim from each slide without speaker notes.
- Static slides may live in one `js/deck.js` registry; they do not need empty lifecycle functions.
- A slide with timers, listeners, charts, media, or WebGL uses a local module and releases those resources on exit.
- Generated visuals stay inside bounded asset containers and pass the checks in [generated_assets.md](generated_assets.md).
- At 50% scale, the claim reads before decorative detail. Body copy is not shrunk to rescue an overloaded layout.
- Preview checks cover every slide, fragments, speaker view, clipping, overflow, and the requested print/PDF path.

## Composition guidance

Prefer a small set of reusable roles: hero, compare, sequence, taxonomy, evidence, and summary. Keep one primary relationship per slide and usually no more than four peer containers. If a fifth item matters, prefer a continuous list, ladder, or table over another equal-weight card.

Use a deck-level visual guideline to define typography, spacing, surfaces, accent semantics, image grammar, and forbidden styles. A generated asset can enrich Reveal mode, but it does not take ownership of the slide.

## Static registry and interactive modules

The reference scaffold keeps static markup in `js/deck.js`. This makes global reordering and visual revision cheap. `js/slides/interactive-check.js` demonstrates the module boundary: install state in `initialize`, remove it in `cleanup`, and keep selectors local to that slide.

Do not force every slide through a dynamic module loader. Use lifecycle machinery only where state exists.
