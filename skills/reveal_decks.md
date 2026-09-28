# Reveal Mode: the Courseware Canvas

Reveal mode builds a lecture or talk as **one continuous, animated sheet**. Reveal.js still provides clicks,
fragments, speaker notes and the speaker view, but the picture lives on a single world layer. Frames sit on it
side by side, a camera moves between them, and on each click elements are drawn, arrive, change state, or split.
The result should read like one printed publication that moves, not a stack of slides.

Designed for Claude Opus 5.5 as the builder; other models are untested (GPT-6 Astra is the suggested alternative).

This replaces the earlier Reveal mode, where every slide was a separate static page of DOM cards. That design
existed because coding agents used to be weak at SVG, motion and layout. A capable agent can now own the whole
picture, and should.

## Acceptance criteria

**Argument**
- `deck_plan.md` states audience, opening question, thesis and closing line; every slide has one claim and says
  what moves on each click.
- With notes hidden, a reader paging through can still recover the argument.

**Motion**
- No click lands on a static bullet page: something is drawn, arrives, changes in place, or the camera moves.
- Elements that stay relevant stay on the sheet and change in place; the camera slides between frames instead of
  cutting.
- Motion explains. Every animation maps to a claim: a thing splitting, a number rolling to its value, a word being
  replaced. The only looping motion is slow idle motion on a hero object, and only where it carries meaning.
- Navigation is exact in both directions: going back one click restores the previous state, and jumping to any
  slide (URL hash, speaker view) renders the right state without replaying the path.

**Look**
- One visual register for the whole deck, written in `visual_guideline.md` before any plate is generated.
- Numbers, labels, charts and quotes are DOM or SVG, never generated pixels. Generated plates are textless.
- Readable on a shared screen: body text 26–40 px at 1080p; nothing below 20 px except source lines.
- Nothing clips, overlaps or scrolls at 1920×1080 or at a laptop-size window.

**Copy**
- On-screen copy and notes follow [copy_workflow.md](copy_workflow.md): drafted by the writer, checked by the
  builder, every fix listed in `validation.md`.
- Every number on screen traces to the source contract; every data frame carries a source line from its first step.

**Verification**
- `tools/shoot.py` has screenshotted every step: zero console errors, zero failed requests, zero requests leaving
  localhost (the deck runs offline), zero unfilled slots.
- At least one independent critic round per [critic_review.md](critic_review.md), with its review saved under
  `verification/critic/`.
- The speaker view (press S) opens and shows notes.

## The engine (in the scaffold)

| File | Owns |
|---|---|
| `js/deck.js` | slide table in speaking order: `id`, running-header `part`, `steps` (clicks), optional `cam` |
| `tools/build_index.py` | the frames; regenerates the block between `FRAMES:BEGIN` and `FRAMES:END` in `index.html` |
| `js/engine.js` | Reveal sections and notes, frame layout, camera, state application |
| `js/copy.js` | the writer's copy, generated from `copy/copy.md` by `tools/copy_to_js.py` |
| `css/deck.css` | tokens and the motion and component vocabulary |

Rules the engine enforces:
- **Slides are addressed by id, not by number.** `data-in="rag_split.2"` means "from the third click of slide
  `rag_split`". Reordering or inserting slides never breaks references.
- **Frames are laid out automatically** in slide order, 2200 px apart. Never hand-place frames on the sheet.
- **State is a pure function of the position.** Presence (`data-in` / `data-out`), class ranges
  (`data-state="split@slide.1"`), split-flap cells, counters, bar heights and label positions are all recomputed
  from the current (slide, step). That is what makes back, jump and reload exact.
- **The camera** is a per-slide or per-step `[dx, dy, zoom]` relative to the frame centre. Long moves arc out and
  back in (zoom dips in log space), so crossing between sections reads as travel.
- **Live content** (charts, WebGL, video) registers `window.DECK_HOOKS[slideId] = { enter(step), leave() }`.
  Keep timers and listeners inside those hooks.

Run order when editing: change the builder or `deck.js` → `python3 tools/build_index.py` → change copy →
`python3 tools/copy_to_js.py` → `python3 tools/shoot.py --out verification/<round>`.

## Motion vocabulary

- **Pen**: SVG paths with `pathLength="1"` draw on via `stroke-dashoffset`. Dashing only hides strokes, so labels
  and dots need their own fade, timed after the strokes.
- **Plate ink-in**: a radial mask grows over an engraving (`.plate`).
- **Rise / pop**: text rises about 18 px; chips pop with a small overshoot. Stagger siblings by 150–250 ms: three
  items appearing at once read as a slide build.
- **Type-on**: key sentences settle in letter by letter (`.type`).
- **Counters** roll to the exact value, and only when stepping forward. **Bars** change height against a dashed
  ghost of the previous value.
- **Split-flap**: a value replaced in place (`data-flap`) shows change over time without a new slide.
- **Split card**: a card cracks on the beat that names the split; the lasting half stays and the expiring half
  tilts away (`.specimen`). A reversed variant exists for when the left half is the one that expires.
- **Camera push-in** of about 5–8% while a detail is discussed keeps a long hold alive.

## Composition guidance

- Frame content box: x 160–1760, y 130–950. The running header and footer (course, part, speaker, folio) sit
  outside it and give the publication feel.
- One primary relationship per frame. A claim is a headline, never a small grey eyebrow.
- A visual device that recurs across frames must look identical every time it returns (the same card, the same
  question pair, the same ladder).
- Text never sits on top of a plate that is being read; retire the plate while text beats run.

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
| Browser print for handouts | Drops every state except one per slide, and all notes | A canvas deck has no stable pages. If a PDF handout is required, choose a print state per slide and export it deliberately. Not yet automated in this repo |
