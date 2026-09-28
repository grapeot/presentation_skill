---
name: presentation
description: >-
  Creates presentation slide decks for AI agents. Defaults to image-generated
  full-slide visuals (outline_visual.md, visual_guideline.md, Reveal.js viewer).
  Also builds Reveal-mode "courseware canvas" decks: one animated sheet with a
  camera, elements drawn or split on each click, textless engraving plates, and
  copy drafted by a writing model and fact-checked by the builder. Use for slide
  decks, keynotes, lectures, teaching decks, speaker notes, or presentation scaffolds.
---

# Presentation Skill

## Goal

Our main objective is to deliver a previewable slide deck directory where every single slide moves the argument forward with one concrete claim. The visual system needs to feel completely coherent from start to finish, and anyone who missed the live presentation should be able to recover the entire core argument just by browsing through the slides on their own.

## Model

We designed and validated the Reveal (canvas) workflow specifically with Claude Opus 5.5 in the builder role. In practice, Opus handles writing the engine code, generating the SVG assets, choreographing motion and layout, and executing all the automated checks. Other models haven't been tested here and are prone to degradation—particularly when it comes to orchestrating motion, dialing in layouts, or sticking faithfully to the verification loop. If you aren't running Opus, GPT-6 Astra is our recommended alternative. Image mode, on the other hand, is far less sensitive to your choice of builder model since full-slide visual composition is handed off directly to the underlying image model.

## Boundaries

**In scope:** Comprehensive deck planning, establishing visual direction, generating slide images, building animated canvas presentations on Reveal.js, crafting local generated plates and iconography, drafting on-screen copy and speaker notes (collaborating with a dedicated writer model whenever available), automated screenshot verification, running independent critic reviews, and serving local previews.

**Out of scope:** Modifying PPTX files, writing open-ended image prompts, and running generic design review checklists. Making raw calls to image generation APIs is the responsibility of the workspace where this skill gets installed (frequently via `image-generation-skill`), rather than this repository.

**Mode rule:** Always default to **image** mode. You should switch to **reveal** mode (our courseware canvas workflow detailed in [reveal_decks.md](reveal_decks.md)) whenever the user explicitly requests an HTML presentation, a lecture or talk that incorporates rich motion, fully editable or exact text copy, code blocks, live data feeds, clickable hyperlinks, multi-step progressive builds, or when they want to avoid full-slide image generation entirely. Keep in mind that your rendering mode and your asset policy are completely separate choices: a Reveal deck typically takes advantage of generated illustration plates, so when a user asks for "no image generation", what you actually want is `reveal` configured with `assets: none`. Crucially, you must never silently downgrade image → reveal simply because image generation encounters an error.

## Acceptance criteria

A deck is considered **done** only when all of the following requirements hold. If any of them fail, the task is not complete.

**Directory & plan**

- Your `deck_plan.md` must clearly state the mode, audience, thesis, and a slide list where each entry specifies one claim and an intentional visual role.
- Speaker notes must exist (in image mode: `speaker_notes.md`; in reveal mode: under the `### notes` sections in `copy/copy.md`, which surface in the speaker view). These notes need to provide spoken context rather than simply parroting on-screen text, and they must satisfy the [speaker-notes spoken-delivery contract](speaker_notes.md).
- A validation note must record exactly what was previewed and detail any items that remain unresolved.
- If a distribution PDF is requested for an image deck, it must be generated using `scripts/presentation-skill export-pdf` (ensuring the compatibility gate passes and the link count strictly matches the overlay plan)—never by printing directly from a web browser.

**Preview**

- Running `start-server.py` must serve `index.html` cleanly with zero errors, and arrow-key navigation must let you step through every single slide.
- If you find that port 8080 or 8000 is already in use, you should pick an alternate available port (like 8765).

**Image mode**

- Your `visual_guideline.md` must establish a unified aesthetic, while `outline_visual.md` needs a dedicated `#### Slide N:` block for each slide containing the **exact** text to appear on screen within the prompts (avoid vague hand-waving like "make it look professional").
- Prompts must clearly separate **visible copy** from internal **design instructions**. Guardrails and constraints like "do not show performance numbers" or "use public data only" must remain strictly as instructional rules, never allowing the model to mistakenly paint them onto the slide canvas.
- Every single `data-background` attribute in `index.html` must map to a real image file located in `generated_slides/`.
- Brand logos, scannable QR codes, software screenshots, and tabular data must always draw from real image files saved in `imgs/`—you must never ask the generative image model to invent them.
- All text rendered on slides must be crisp and easily legible; any garbled or distorted characters represent an outright failure (fix this by streamlining your copy, running another render, or layering exact HTML/CSS typography over top).

**Reveal mode (courseware canvas)**

- The presentation must satisfy every single criterion laid out in [reveal_decks.md](reveal_decks.md): operating on a single world canvas steered by a camera, maintaining state that depends strictly on the current (slide, step) coordinate, employing animations that actively support the argument, sticking to one consistent visual register, and remaining easily readable when projected or shared on screen.
- All slide copy must adhere to the process outlined in [copy_workflow.md](copy_workflow.md): drafted by a dedicated writing model whenever one is available (or by the builder working against those exact same contracts), with every single drift correction tracked in `validation.md`.
- Illustration plates must follow [generated_assets.md](generated_assets.md): locked into a single cohesive aesthetic, completely free of text, and rendered as crisp ink over a transparent background.
- Automated runs of `tools/shoot.py` must report zero console errors, zero failed requests, zero requests attempting to leave localhost, and zero unfilled slots; furthermore, at least one [critic round](critic_review.md) must be completed and stored under `verification/critic/`.

**Cross-mode awareness**

- Before you begin modifying files, make sure to inspect the root files in the scaffold for the active mode and take a moment to look over `examples/<other-mode>/` so you understand exactly which architectural paradigm you are working within.

## Available resources

**Scaffold (start here for a new deck)**

```bash
bash scripts/presentation-skill "Topic" --mode image --output deck_work
bash scripts/presentation-skill "Topic" --mode reveal --assets mixed --output deck_work
bash scripts/presentation-skill "Topic" --request "HTML only, no image generation" --output deck_work
```

**PDF export (image decks — the default way to produce the distribution PDF)**

```bash
bash scripts/presentation-skill export-pdf deck_work --check-only   # compatibility gate only
bash scripts/presentation-skill export-pdf deck_work --output deck_work/handout/slides.pdf
```

This pipeline compiles the PDF directly from the high-resolution slide images (lossless, avoiding browser print quirks entirely) and embeds every `overlay-data` hotspot as a real PDF link annotation sharing the exact rect and padding of the HTML overlay, ensuring clicking works identically across PDF and HTML. The built-in compatibility gate requires every section to consist strictly of a background image plus speaker notes, failing loudly if anything violates that structure—so if it ever flags INCOMPATIBLE, you should fix the slide markup or fall back to manual export; never ship a silently lossy PDF. Note that this feature requires the `[pdf]` dependency extra (img2pdf + pypdf).

Once initialization wraps up, read `deck_work/README.md`. You will find the active mode files sitting right at the deck root, while the alternate mode lives under `examples/`.

**Reveal (canvas) loop** (inside a reveal scaffold):

```bash
npm install && npm run vendor            # Reveal + fonts into vendor/ (runs offline afterwards)
python3 tools/build_index.py             # regenerate frames from the builder
python3 tools/copy_to_js.py              # copy/copy.md -> js/copy.js (prints spoken minutes)
python3 tools/shoot.py --out verification/round1   # every step, contact sheets, offline/error report
```

**Preview**

```bash
cd deck_work
uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python start-server.py --port 8765 --no-browser
```

**Image rendering** (inside scaffolded deck, uses workspace credentials via `.env`)

```bash
PYTHONPATH=. python tools/generate_slides.py --outline outline_visual.md
# Draft batch (default): generated_slides/
# Final batch: --size 4K --quality high --output-dir generated_slides_4k
```

Our OpenAI backend integrates with the GPT Image 2.5 family, which offers two distinct variants at the same price point:

- `gpt-image-2.5-flare` — Optimized for speed, making it ideal for rapid draft iterations.
- `gpt-image-2.5-sunburst` — Engineered for precision, making it the choice for final presentation renders.

The generator selects variants based on your target resolution: **1K → flare**, while **2K/4K → sunburst**. You can always override this by passing `--variant flare|sunburst` (leaving it as `auto` will follow the resolution rule). Image quality defaults to **`auto`**, but you can pin it explicitly using `--quality low|medium|high|xhigh|max|auto`. Keep in mind that the 2.5 quality scale is much more cost-effective than GPT Image 2: setting 2.5 to `high` costs roughly one-fourth of what GPT Image 2 `high` cost, while 2.5 `max` roughly matches that older `high` price tier.

Whenever a slide requires a combination of visual assets—like a navigation bar, a logo, and a chart or QR code—list all of them under `Asset` in `outline_visual.md`. Because GPT Image 2.5 supports multiple input images in a single API call, the generator passes them through directly; simply name each asset and describe its exact placement within your prompt.

**Mode → root artifacts**

| Mode | Root artifacts |
|---|---|
| image | `outline_visual.md`, `visual_guideline.md`, `generated_slides/`, `tools/`, image `index.html` |
| reveal | `index.html`, `js/deck.js`, optional `js/slides/*.js`, `imgs/`, `visual_guideline.md` |

## Methodology (suggestions, not mandatory order)

- Focus on advancing one concrete claim per slide; prefer clear, assertive statements over passive topic titles like "Architecture".
- If you are writing direct-read presentation scripts or carrying out major speaker-note revisions, load [speaker_notes.md](speaker_notes.md). It establishes the breath test, natural transition handoffs, the factual-fidelity gate, and batch review practices for long decks.
- When creating image decks, establish visual consistency early through `visual_guideline.md` along with shared style reference assets, and only trigger image generation once the outline copy is firmly locked in.
- For text-heavy image slides, keep title zones wide, put a ceiling on visible labels, and explicitly instruct the model to use normal-width typography. Placing long blocks of copy inside narrow columns frequently tempts image models to simulate condensed fonts or horizontally compress character shapes.
- For Reveal presentations, plan out your entire canvas sheet (defining frames, deciding what shifts on each click, and establishing recurring visual motifs) before writing markup; address slides by their semantic id, and make sure to read [reveal_decks.md](reveal_decks.md), [copy_workflow.md](copy_workflow.md) and [critic_review.md](critic_review.md).
- Audit every single example against your target audience before building: retain a reference only if it helps these specific listeners understand faster or believe more, not simply because it was present in the source material.
- In Reveal mode, bring in illustration plates only when the visual metaphor actively carries the argument; empty white space on its own is never a reason to tack on decorative elements.
- Prefer the workspace's dedicated image-generation skill whenever it is available.
- When building image decks that display URLs, QR codes, or interactive embeds, add a clickable HTML overlay layer as outlined in [docs/clickable_overlays.md](../docs/clickable_overlays.md)—define the target zone in the prompt, measure the rendered element's bounding box using computer vision, inject padded `<a>` or iframe hotzones, and verify alignment with a draw-back visual check.

## Known traps

| Trap | How it shows up | What to do |
|---|---|---|
| Wrong install path | An agent tries to load a stale `.agents/skills/` directory or an injected path that simply does not exist | Make sure you follow the installing workspace's skill index or `WORKSPACE.md`. The canonical repo skill lives at `skills/skill_presentation.md` in the `presentation_skill` package. |
| Treating Python helpers as an AI planner | Assuming `deck_plan.py` or the CLI will write slide content for you | Remember that Python scripts only set up directory scaffolds and enforce validation rules. The agent is responsible for writing `deck_plan.md`, drafting outlines, and authoring modules. |
| Silent mode downgrade | When the image generation API errors out, the agent quietly falls back to Reveal mode without checking | Stop immediately and explain the blocker; keep your source artifacts intact, and only change modes if the user explicitly authorizes it. |
| Model-invented text | The model generates unscannable QR codes, garbled alien glyphs, or made-up corporate logos | Place exact pixel assets in `imgs/` and reference them through the outline Asset sections; always define exact, readable copy directly in your prompts. |
| Internal constraints painted onto slides | A prompt includes instructions like "no private numbers" or "public data only", and the model visibly paints those caveats right onto the slide canvas | Keep negative constraints completely separate from visible text. Frame rules as "Do not render any text about X" and explicitly list the exact headings and labels the model is permitted to draw. |
| Horizontally squeezed typography | Lengthy titles or card labels appear uncomfortably narrow or horizontally compressed, particularly inside fixed-width columns | Trim the visible wording, let the title span full width, and explicitly add: "Use normal-width Inter or Helvetica-style sans-serif, not condensed. Do not horizontally scale or compress letters; reduce font size or wrap at word boundaries." If the problem persists, move the text into an HTML/CSS overlay. |
| Confusing composition with assets | Treating a Reveal slide as an image-mode slide just because it incorporates a generated plate | Assign exactly one composition owner to each slide: Reveal controls geometry and exact copy, while generated plates play a supporting visual role. |
| Canvas-specific traps | Encountering white boxes around engravings, stage overlays that never disappear, climax shots pulled back to thumbnail size, or numbered slide references | Consult the comprehensive traps table in [reveal_decks.md](reveal_decks.md). |
| Decorative asset filling | Spotting empty space on a slide and dropping in arbitrary icons that distract from your core message | Only introduce an asset when it genuinely speeds up comprehension, differentiates parallel concepts, or clarifies an underlying mechanism. |
| Skipping examples | Newly authored slides drift away from the contracts established by the scaffold | Take time to read the root scaffold files and browse through `examples/` before writing; model your new slides directly on those proven patterns. |
| Preview without server | Attempting to open `index.html` directly with the `file://` protocol, which breaks ES modules and CDN dependencies | Always run `start-server.py` to preview the deck, and switch to an alternative port if default ports are occupied. |
| English/Mixed Prompts in Chinese Decks | Combining English and Chinese words in image prompts intended for Chinese presentation slides | Make sure you use **100% pure Chinese prompts** (apart from standard CLI parameters like `--ar 16:9`). Any stray English words (such as "vs", "chart", or "mockup") will prompt the model to paint garbled, meaningless Latin glyphs onto the slide canvas. |
| Bracketed English Translations | Including paired translations like "中文 (英文)" or "中文（英文）" inside text overlays or speaker notes | **Never** include bracketed translations (such as "事实包 (Information Pack)"). They add zero value for Chinese-speaking audiences while heavily cluttering the visual hierarchy. |
| Non-Visual Transition Logical Flow | Leaving explanatory notes in your outline about logical flow while the actual slide imagery feels disconnected | Conceptual transitions must be **visualized** on screen. Instruct the model to render a consistent **Top Navigation Bar / Flow Indicator** in your prompt (highlighting the current active step) and echo that structure in the text overlay. |
| Abstract or Vague Chart Prompts | Giving the model vague prompts like "draw a radar chart of AI sychophancy/quality metrics" | Spell out the **exact dimensions** (for example, five dimensions: "AI腔词汇比率", "空洞无事实比率") alongside precise values and comparison pairings in the prompt. Never leave abstract figures for the model to guess. |
| PYTHONPATH Missing for Generator | Running `generate_slides.py` crashes with ModuleNotFoundError: No module named 'tools' | Always prefix your execution with `PYTHONPATH=.` when invoking generation tools from local slide directories so Python resolves internal modules properly. |
| Multi-image assets | Attempting to pass multiple reference images—like a navbar, logo, and QR code, or a chart and style reference—under `Asset` | Include every required pixel reference in your outline's `Asset` list. Because GPT Image 2.5 natively supports multiple input images in a single request, `tools/generate_slides.py` forwards them all at once without manual stacking. Just be sure to name each asset and clearly state where it belongs inside the prompt (for instance, 「导航条贴顶左对齐，Logo 居中，二维码嵌入右侧卡片」). |
| Hallucinated Quantitative Chart Details | Asking the generative image model to draw exact numerical graphs, such as precise bar charts or line plots | Always generate exact quantitative charts ahead of time using Python + Matplotlib as a clean PNG image, pass that as the single `Asset`, and instruct the image model to accurately follow its data layout. |
| Painted links that don't click | A clickable pill or QR caption is painted directly into the slide graphic so viewers cannot click it, or overlay coordinates estimated from prompts misalign with visual targets by ~5% | Set up an HTML overlay layer as described in [docs/clickable_overlays.md](../docs/clickable_overlays.md): extract coordinates by visually measuring the rendered slide after generation (rather than estimating from prompts), add 1.5% padding to hitboxes, and verify every hotspot using a Pillow draw-back test. |
| Printed-PDF link 404s / tiny pages | Using `?print-pdf` rewrites overlay links to match the visible pill text (causing `x.com/a` to 404 when the real href is `x.com/a.html`), while un-sized Reveal slides print as shrunken boxes in the center of the page | Avoid printing from the browser entirely: run `scripts/presentation-skill export-pdf <deck>` to assemble the PDF straight from image files and inject overlay targets as real PDF annotations. Only resort to browser printing if the compatibility gate flags that the deck is not a pure image deck. |
| Dense text exhibits corrupted on hi-res re-render | A data-dense screenshot (like a financial table or report) looks fine in a draft render, but the 4K final batch corrupts key numbers ("$25.11" → "$2.11"), and repeated re-rolls just scramble different numbers | Stop re-rolling images. Instead, composite the content deterministically: find the target frame within the generated slide (detecting its bounding borders with code), take a fresh high-fidelity capture of the true source (such as a headless-Chrome screenshot of your styled document adjusted to the frame's aspect ratio), and paste those exact pixels inside the container using Pillow. That way, the model provides the outer frame while your data remains pristine ground truth. |

## Additional resources

- If you need detailed contracts, directory layouts, and setup instructions, head over to [reference.md](reference.md).
- To dive deep into the canvas contract, internal engine mechanics, and edge cases, take a look at [reveal_decks.md](reveal_decks.md).
- For a breakdown of how the writer and builder divide up responsibilities and catch factual drift, read [copy_workflow.md](copy_workflow.md).
- To see how to run an independent visual review on your rendered frames, check out [critic_review.md](critic_review.md).
- When you are creating icons or conceptual illustrations to support your slides, refer to [generated_assets.md](generated_assets.md).
- If you are preparing full spoken scripts or revising in-depth speaker notes, be sure to consult [speaker_notes.md](speaker_notes.md).
- For instructions on layering clickable hotspots and interactive widgets over image slides, follow [docs/clickable_overlays.md](../docs/clickable_overlays.md).
