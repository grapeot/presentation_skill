# Courseware Canvas — a lecture deck that moves like an explainer

Progressive-disclosure support for `skill_presentation.md`. Read this when a
talk or lecture should feel like one continuous, animated publication instead
of a stack of slides, and the agent building it can write motion, SVG and
layout code itself.

## Metadata

- **Type**: Workflow + BestPractice
- **Use when**: a lecture, guest talk or course module where the speaker clicks
  through (Reveal navigation, speaker view, notes) but the picture should move:
  a camera across one sheet, elements that persist and change, diagrams drawn
  on cue.
- **Not for**: image-mode decks (use the root skill), decks whose owner edits
  slides by hand in a GUI, and decks that must print to PDF page-for-page
  (a moving sheet has no stable pages; ship a separate handout if one is needed).
- **Output**: a static site (`index.html`, `js/`, `css/`, `assets/`, vendored
  Reveal and fonts) plus `deck_plan.md`, `copy/` and `speaker_notes` embedded
  in the deck, and `validation.md`.

## Why this exists

The Reveal and image modes in this repo were written when coding agents were
weak at SVG, animation and layout, so they pushed visuals into image models and
kept the DOM to cards and text. A capable agent can now own the picture itself.
Keep what still holds from the root skill (one claim per step, exact copy in
the DOM, real assets for anything that must be true, speaker notes that add
rather than repeat) and drop the defensive parts (every slide is a separate
static page; generated images carry the composition).

## Acceptance criteria

The deck is done when all of the following hold.

**Argument**
- `deck_plan.md` states the audience, the opening question, the thesis, and a
  step list. Every step (slide or fragment) has one claim and names what moves.
- A reader who pages through with notes hidden can still recover the argument.

**Motion**
- No step lands on a static bullet page: at each step something is drawn,
  arrives, changes state, or the camera moves to it.
- Elements that stay relevant stay on the sheet and change in place; the camera
  slides between sets instead of cutting.
- Motion explains. Each animation maps to a claim: a thing splitting, a
  quantity growing, a word being replaced. Nothing loops for decoration while
  the speaker talks, except slow idle motion on a hero object.
- Navigation is reversible and deterministic: going back one step restores the
  previous state exactly, and jumping to any slide (overview, URL hash) renders
  the right state without replaying the path.

**Look**
- One visual register for the whole deck (paper, ink, type, plate technique),
  written in `visual_guideline.md` before any plate is generated.
- Generated plates are printed onto the page (multiply onto the paper colour),
  share one style paragraph, and contain no text, numbers or logos.
- Numbers, labels, charts and quotes are DOM or SVG, never generated pixels.
- At 1920x1080 and at a laptop-size window, nothing clips, overlaps or
  scrolls; text stays at readable size on a shared Zoom screen (body ≥ 28 px
  at 1080p, labels ≥ 20 px).

**Copy**
- On-screen copy and speaker notes were drafted by the writing model (see
  "Division of labour"); the builder made only surgical fact-drift fixes, each
  listed in `validation.md`.
- Every number on screen traces to a source line in `copy/source_contract.md`;
  data steps carry a small source line.

**Verification**
- Every step has a screenshot from a headless browser run, reviewed on a
  contact sheet; an independent critic reviewed at least one round
  (`procedural-video-frames/critic_prompt.md`, adapted to slides).
- The deck runs offline: Reveal, fonts and plates are vendored locally; a
  network-blocked browser run shows no failed requests.

## Division of labour

| Role | Who | Owns |
|---|---|---|
| Editor and builder | the main agent | thesis, step list, visual system, motion, code, fact checks, final acceptance |
| Writer | Antigravity CLI (`gemini-3.8-flash-high`), fresh session per task | on-screen copy and speaker notes, from a task packet |
| Plates | image generation skill (`gpt-image-2.5-sunburst`) | textless engraving-style illustrations |
| 3D (optional) | Blender via the GPT 3D skill | a hero object that needs real light or parallax; skip unless a claim needs it |
| Critic | a fresh sub-agent that sees only screenshots and the rubric | ranked visual problems |

The writer is better at prose; the builder is better at motion and at following
constraints. The writer does not follow instructions reliably, so the builder
checks the draft against the source contract and pulls back every drift
(numbers, qualifiers, claim strength, invented examples), and does not restyle
the prose while doing so.

Writer task packet (all in a minimal scratch dir, absolute paths):
- `source_contract.md`: facts, numbers with sources, and the speaker's positions,
  with qualifiers that must survive.
- `deck_brief.md`: audience, opening question, thesis, and per step: the claim,
  what the picture shows, the copy slots with word limits.
- `voice_contract.md`: the spoken register (podium voice, see
  `speaker_notes.md` in this repo) and on-screen register (short, declarative,
  no slogans).
- Output: one `copy.md` with a fixed per-step schema, so the builder can parse
  it.

## Building the canvas

Approach that worked (suggestion, not a mandate):

- **Reveal owns navigation, notes and speaker view; a fixed stage owns the
  picture.** Reveal sections are empty carriers of notes and fragments. A
  full-viewport stage layer holds one large sheet (the "world") designed at a
  fixed resolution and scaled to fit. On `ready`, `slidechanged` and
  `fragmentshown/hidden`, compute the global step index and apply that step's
  state.
- **State is a function of the step index, not of history.** Each element
  declares the step range where it is present (and optional per-step variants).
  The camera is a per-step `(x, y, zoom)` target. Applying a step sets classes
  and the camera transform; CSS transitions do the motion. This makes back,
  jump and overview correct for free.
- **Motion vocabulary** (from `procedural-video-frames/motion.md`, translated to
  the DOM): pen-drawn SVG paths via stroke-dashoffset, plates that ink in via an
  animated mask, chips that pop with a small overshoot, counters that roll to
  the exact value, bars that grow with hatching, text that types on for key
  sentences, a slow push-in while a detail is discussed.
- **Stagger siblings** (150–250 ms). A list that appears at once reads as a
  slide build.

## Plates

- Lock the style on one plate, then generate the rest in parallel (4–6
  concurrent) with the same style paragraph: medium, line technique, paper,
  "no text, no border, isolated subject, plain paper background".
- Normalise the paper to white and print with `mix-blend-mode: multiply` so
  only the ink lands on the page.
- One subject per plate; a metaphor the audience recognises without a caption
  (a card catalogue for retrieval, a switchboard for protocols, scaffolding for
  a temporary structure).

## What the critic kept finding

On the first deck, two critic rounds moved the scores from 5–7 to about 7 on every criterion. The same design failures came up repeatedly, so check for them before the critic sees anything:

- **A claim set as an eyebrow.** A 16 px grey caps label carrying the slide's actual claim reads as metadata. Set the claim as the headline; keep eyebrows for navigation.
- **A foreign widget.** A dark UI panel (a split-flap board) in a paper-and-ink deck reads as SaaS. Reprint it in the deck's material: ink on paper, hairline rules, colour only on what changes.
- **An equal-weight card grid at the climax.** Four identical cards read as a template. Give them material (plates, the patch still attached) and let the click change them physically.
- **Closing lines in two voices.** Some endings in grey sans, others in serif, makes them read as captions. Pick one voice for closing lines.
- **Italics and decorative numerals everywhere.** Then nothing lands. Reserve italics for one recurring device, and keep large section numerals clear of type or drop them.
- **Diagrams as thin vector boxes.** A rectangle with an X reads as a placeholder. Draw tension as tension (springs along the edges), put the choice inside (a dot pulled toward two corners), and caption it with a claim, not the labels again.
- **A third accent sneaking in.** Gold rules next to blue/vermilion semantics weakens both. Structural rules are ink.

## Known traps

Observed on the first deck built with this skill (a 40-minute, 19-slide, 67-step
guest lecture, September 2026).

| Trap | What it looked like | What to do |
|---|---|---|
| `mix-blend-mode: multiply` does nothing inside the transformed world | Every engraving showed a white rectangle on the paper | The world layer isolates blending, and its backdrop is transparent. Convert plates to ink on alpha (rgb = ink colour, alpha = 1 − luminance) and drop blend modes |
| A stage-level overlay with only `data-in` | A pull-back headline stayed on every later slide and covered their lower halves | Anything outside the world (fixed on the stage) needs an explicit `data-out`. Better: put the moment in the world and move the camera to it |
| Payoff shot at 0.2× zoom | The pull-back over four specimen cards read as a row of thumbnails | Use the zoomed-out view only as a transition; land the payoff on a new set at 1× (here, a band below the cards with only the surviving halves) |
| Pen-drawn SVG labels | Dots and corner labels showed before their strokes were drawn | `stroke-dashoffset` only hides strokes. Hide `text`/`circle` separately and fade them in after the lines |
| Decorative line visible before its beat | The crack meant to split a card was drawn from the first frame | Tie every mark to the step that explains it; draw it on that step |
| Writer drift is semantic as well as factual | The writer put the patch into a card's "problem" slot, stretched "once the field settles" into "after decades", invented anecdote details (message counts, example queries), and added causal claims to a pay chart | Check every slot against the claim it must carry, as well as every number. Record each fix in `validation.md` |
| Harness and critic share an output directory | A partial re-shoot overwrote the contact sheet the critic was reading | Give each critic round its own frozen shots directory |
| `xargs -I` with long prompts | "command line cannot be assembled, too long" before any plate rendered | Generate plates from a small Python thread pool |
| A text column over a plate | Story beats laid over the card-catalogue engraving were hard to read | Retire the plate while the text beats run, and bring it back on the next visual beat |
