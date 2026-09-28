# HTML Mode: the Canvas Deck

HTML mode generates the deck as a web page: **one continuous, animated sheet** without slide borders. The agent writes the picture directly in HTML, CSS and SVG. It works for a keynote, a lecture, a pitch, a product walkthrough or an explainer alike. Reveal.js is only the plumbing underneath (clicks, speaker notes and the speaker view); the entire picture lives on a single world layer. Frames sit on it side by side, a camera moves smoothly between them, and on each click elements are drawn, arrive, change state, or split. In practice, the result should read like one printed publication that moves, rather than a traditional stack of slides.

This setup was designed for Claude Opus 5.5 as the builder; other models are untested (GPT-6 Astra is the suggested alternative).

This replaces our earlier HTML mode, where every slide was a separate static page of DOM cards. That design existed because coding agents used to be weak at SVG, motion and layout. Today, a capable agent can own the whole picture, and should.

## Acceptance criteria

**Argument**
- `deck_plan.md` must state the audience, opening question, thesis and closing line; every slide must have one claim and say what moves on each click.
- With notes hidden, a reader paging through must still be able to recover the argument.

**Motion**
- No click should ever land on a static bullet page: something is drawn, arrives, changes in place, or the camera moves.
- Elements that stay relevant stay on the sheet and change in place, and the camera slides between frames instead of cutting.
- Motion explains. Every animation maps directly to a claim: a thing splitting, a number rolling to its value, or a word being replaced. The only looping motion allowed is slow idle motion on a hero object, and only where it carries meaning.
- Navigation must be exact in both directions: going back one click restores the previous state, and jumping to any slide (via URL hash or the speaker view) renders the right state without replaying the path.

**Look**
- You must maintain one visual register for the whole deck, written down in `visual_guideline.md` before any plate is generated.
- Numbers, labels, charts and quotes must be DOM or SVG, never generated pixels. Generated plates must be textless.
- The deck must be readable on a shared screen: body text should be 26–40 px at 1080p; nothing should be below 20 px except source lines.
- Nothing clips, overlaps or scrolls at 1920×1080 or at a laptop-size window.

**Copy**
- On-screen copy and notes must follow [copy_workflow.md](copy_workflow.md): drafted by the writer, checked by the builder, with every fix listed in `validation.md`.
- Every number on screen must trace back to the source contract; every data frame must carry a source line from its first step.

**Verification**
- `tools/shoot.py` must have screenshotted every step: zero console errors, zero failed requests, zero requests leaving localhost (the deck runs offline), and zero unfilled slots.
- You must complete at least one independent critic round per [critic_review.md](critic_review.md), with its review saved under `verification/critic/`.
- The speaker view (press S) must open and show notes.
- If a PDF handout is part of the deliverable, `export-pdf` must pass its checks and its contact sheet must show every slide at a complete print state (see "PDF handout").

## The engine (in the scaffold)

| File | Owns |
|---|---|
| `js/deck.js` | The slide table in speaking order: `id`, running-header `part`, `steps` (clicks), and optional `cam` |
| `tools/build_index.py` | The frames; regenerates the block between `FRAMES:BEGIN` and `FRAMES:END` in `index.html` |
| `js/engine.js` | Navigation and notes (via Reveal.js), frame layout, camera movement, and state application |
| `js/copy.js` | The writer's copy, generated from `copy/copy.md` by `tools/copy_to_js.py` |
| `css/deck.css` | Design tokens along with the motion and component vocabulary |

Rules the engine enforces:
- **Slides are addressed by id, not by number.** For example, `data-in="rag_split.2"` means "from the third click of slide `rag_split`". That way, reordering or inserting slides never breaks references.
- **Frames are laid out automatically** in slide order, 2200 px apart. Never hand-place frames on the sheet.
- **State is a pure function of the position.** Presence (`data-in` / `data-out`), class ranges (`data-state="split@slide.1"`), split-flap cells, counters, bar heights and label positions are all recomputed from the current (slide, step). That mathematical clarity is what makes back, jump and reload exact.
- **The camera** is a per-slide or per-step `[dx, dy, zoom]` relative to the frame centre. Long moves arc out and back in (with zoom dipping in log space), so crossing between sections reads as travel.
- **Live content** (such as charts, WebGL, or video) registers via `window.DECK_HOOKS[slideId] = { enter(step), leave() }`. Keep timers and listeners inside those hooks.
- **Touch navigates** on phones and tablets: tap the left 30% to go back, anywhere else to advance, or swipe. Links, buttons and form fields are skipped; mark any other interactive element `data-no-nav`.

Here is the run order when editing: change the builder or `deck.js` → `python3 tools/build_index.py` → change copy → `python3 tools/copy_to_js.py` → `python3 tools/shoot.py --out verification/<round>`.

## Motion vocabulary

- **Pen**: SVG paths with `pathLength="1"` draw on via `stroke-dashoffset`. Dashing only hides strokes, so labels and dots need their own fade, timed after the strokes.
- **Plate ink-in**: A radial mask grows smoothly over an engraving (`.plate`).
- **Rise / pop**: Text rises about 18 px; chips pop with a small overshoot. Stagger siblings by 150–250 ms: three items appearing at once read as a slide build.
- **Type-on**: Key sentences settle in letter by letter (`.type`).
- **Counters** roll to the exact value, and only when stepping forward. **Bars** change height against a dashed ghost of the previous value.
- **Split-flap**: A value replaced in place (`data-flap`) shows change over time without requiring a new slide.
- **Split card**: A card cracks on the beat that names the split; the lasting half stays and the expiring half tilts away (`.specimen`). A reversed variant also exists for when the left half is the one that expires.
- **Camera push-in** of about 5–8% while a detail is discussed keeps a long hold alive.

## SVG: the deck's drawing layer

Most of what moves in a canvas deck is hand-written SVG, not generated pixels. The agent writes it inline in `tools/build_index.py`, so every line, label and number stays exact and animatable.

- **Use SVG for anything with structure**: diagrams, pipelines, timelines, charts, arrows, brackets, callout circles, cracks and connectors. These draw on with the pen, and their labels are real `<text>`.
- **Use generated plates for material**: engravings, objects and scenes that give a metaphor weight. The template's `imgs/cpu-blueprint.svg` shows the middle ground, a line illustration kept as an SVG file and inked in like a plate.
- **Keep SVG in the deck's register**: stroke in the ink colour, use the two accent colours only where they carry meaning, and fill areas with hatching patterns rather than gradients. Set `pathLength="1"` on any path that should draw on.
- **Size text in SVG user units that match the frame** (one unit = one pixel at 1080p), so the readability limits above still apply.
- **Draw tension as tension.** A spring, a strained line or a bar pushing past its old ghost says more than a labelled box.

## Composition guidance

- Frame content box: x 160–1760, y 130–950. The running header and footer (event or series, part, speaker, folio) sit outside it and give the publication feel. Drop them if the occasion calls for a cleaner stage.
- Keep one primary relationship per frame. A claim is a headline, never a small grey eyebrow.
- A visual device that recurs across frames must look identical every time it returns (the same card, the same question pair, the same ladder).
- Text never sits on top of a plate that is being read; retire the plate while text beats run.

## PDF handout

`scripts/presentation-skill export-pdf <deck>` turns the deck into a PDF with one page per slide. It serves the deck on a private loopback port, opens it in headless Chromium at 1920×1080 with screen media (Reveal's print stylesheet never applies), switches off transitions and CSS animations, and calls `deckGoto(i, step)` for each slide's print state. It waits until the page stops changing, then prints that state as one 1920×1080 page with backgrounds. The pages are merged into one PDF, with resources that repeat across pages (a grain layer, a recurring plate) stored once. Text stays vector and searchable, and `<a href>` elements become PDF links.

- **Print state.** By default this is the slide's last step. To print another step, set `print` on the slide entry, e.g. `S("board", P2, 5, null, { print: 3 })` with the scaffold's `S` helper. An invalid `print` value fails the export.
- **Handout layout.** Some slides hide information in every single state: a split-flap board that shows one year at a time, or a card that replaces its own text. For these, write a dedicated handout arrangement in CSS. During export `<html>` carries the class `pdf-export` and the attributes `data-print-slide="<id>"` and `data-print-step="<n>"`, so a rule such as `html.pdf-export[data-print-slide="board"] .flap { … }` can print the board's years as rows. The rule never matches in the live deck.
- **Speaker notes.** `--with-notes` follows every slide page with a notes page of the same size. The notes come from `window.COPY[id].notes`, or from the slide's Reveal `<aside class="notes">`. They are set in the deck's body font on its paper colour, in two columns, with a header naming the part, the slide number and the id. The font size shrinks from 30 px to 16 px to fit; notes that do not fit even at 16 px fail the export. A full page (rather than a band under the slide) keeps the slide at full size and keeps long scripts readable.
- **Effects that viewers render differently.** Chromium's PDF backend prints some paint effects in forms that PDF viewers do not render the way the browser does. A blurred `box-shadow` becomes a fill under a luminosity soft mask, and Apple PDFKit (Preview) ignores that mask and paints a solid grey box. A repeating gradient or an SVG `<pattern>` becomes one low-resolution raster tile, which shows as moiré. A CSS mask becomes a luminosity soft mask too. Before each page is printed, the exporter lets the browser redraw these effects:
  - blurred outer shadows are redrawn as PNG layers behind their element, at 2× resolution;
  - repeating and conic gradient backgrounds are redrawn as PNG backgrounds, also at 2×;
  - SVG pattern fills are tiled out into vector geometry;
  - CSS masks that are fully opaque over their element (a plate that has finished inking in) are dropped.

  The page still looks like the live slide. Every change is undone before the next state is applied. Anything the exporter cannot redraw is printed as is and reported as a warning. That covers a partially transparent mask, a shadow on an element that clips its overflow, and a pattern with unusual units.
- **Images.** `<img>` sources larger than 2× their displayed size are downsampled to 2× (`--image-scale`, 0 keeps the originals). After merging, large RGB images are re-encoded as JPEG at quality 85 (`--image-quality`, 0 keeps them lossless). Soft masks stay lossless. Large embedded images are what make Preview draw a page's images in pieces while it decodes them.
- **Checks.** The export fails loudly when the page count does not match the slide table (plus the notes pages); when there is any console error, page error or failed local request, or any request leaves localhost; when a copy slot is unfilled (`.missing`); when a web font fails to load; or when a page is not exactly one 1920×1080 page. It also writes `<name>_contact_NN.jpg` next to the PDF (rendered with pymupdf or poppler's `pdftoppm`); a state with a running animation at capture time is reported. Read the contact sheet: every page should show the full print state, with nothing half-faded, clipped or blank, and in the deck's fonts.
- **What it relies on.** Only the engine contract: `window.DECK`, `window.deckGoto(i, step)` applying state without animation, the `missing` class on unfilled slots, and `window.COPY`. It uses no template CSS classes, so decks with their own engine copy and stylesheet export the same way. Motion that is driven from JavaScript (`requestAnimationFrame` counters, `DECK_HOOKS` content) is given up to 4 s to settle; a page that never settles is printed as is, with a warning. An infinite idle animation is printed at its first frame.

## Known traps

| Trap | What it looked like | Do this |
|---|---|---|
| `mix-blend-mode: multiply` inside the transformed world | Every engraving showed a white rectangle | Blending is isolated inside the world layer. Convert plates to ink on transparent (see [generated_assets.md](generated_assets.md)) and use no blend modes |
| A stage-level overlay with only `data-in` | A headline stayed on every later slide and covered their lower halves | Put the moment in the world and move the camera to it. Anything fixed on the stage needs an explicit `data-out` |
| A payoff shot at 0.2× zoom | A pull-back over four cards read as a row of thumbnails | Use a far zoom only as a transition. Land the payoff on its own frame at 1× |
| Pen labels visible early | Dots and labels appeared before their lines were drawn | Hide `text` and `circle` separately; fade them in after the strokes |
| Decorative marks before their beat | A crack was visible on a card before the split | Tie every mark to the click that explains it |
| Numbered slide codes | Inserting one slide shifted every later reference | Address slides by id |
| Hand-placed frame coordinates | A reorder meant recomputing every `left:` | Let the engine lay out frames in slide order |
| Harness and critic sharing a directory | A partial re-shoot overwrote the contact sheet the critic was reading | Give every critic round its own frozen `--out` directory |
| Stale server port | The owner saw an older deck, or someone else's app, on the expected port | Check what is listening before starting the server; say which URL you started |
| Browser print for handouts | Drops every state except one per slide, and all notes | A canvas deck has no stable pages. Run `scripts/presentation-skill export-pdf <deck> [--with-notes]`, which prints each slide's chosen state (see "PDF handout" above), then read the contact sheet |
| Grey boxes or moiré in Preview | A PDF printed straight from the browser shows grey rectangles around shadowed cards and banded hatching in Preview, although other viewers look fine | Export with `export-pdf`, which redraws those effects before printing. Check the pages in Preview (or another PDFKit-based viewer) as well as in the contact sheet |
| Final state hides information | The printed page shows only the last beat: a flap board showing this year, a struck-through list without its replacement | Set `print: <step>` on the slide, or give the slide a handout layout under `html.pdf-export[data-print-slide="<id>"]` |
| Portrait phone in scroll view | Below 435 px wide, Reveal 5 switched to its scroll view and bypassed the canvas: `#/9` opened the title slide and navigation stopped working | Keep `scrollActivationWidth: null` in `Reveal.initialize` (the scaffold sets it) |
| Relying on Reveal's swipe | Swiping did nothing on a phone. The Reveal layer has `pointer-events: none`, so Reveal's own swipe never fires, and pointer-event handlers are cancelled on horizontal drags because the browser claims them as pans | Keep the engine's touch-event handler and `touch-action: manipulation`; do not rewrite it with pointer events |
