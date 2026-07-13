---
name: presentation
description: >-
  Creates presentation slide decks for AI agents. Defaults to image-generated
  full-slide visuals (outline_visual.md, visual_guideline.md, Reveal.js viewer).
  Falls back to HTML/JS module decks when the user requests no image generation,
  editable HTML, or interactive slides. Use for slide decks, keynotes, teaching
  decks, speaker notes, or presentation scaffolds.
---

# Presentation Skill

## Goal

Deliver a previewable slide deck directory where every slide advances one concrete claim, the visual system is coherent, and a reader who missed the talk can still recover the argument from the slides alone.

## Boundaries

**In scope:** deck planning, visual direction, image-rendered slides, HTML/JS module slides, speaker notes, local preview via Reveal.js.

**Out of scope:** PPTX editing, generic image prompting, design review checklists. Image API calls belong to the installing workspace (often `image-generation-skill`), not this repo.

**Mode rule:** Default to **image** mode. Switch to **html** only when the user explicitly asks (e.g. "HTML only", "no image generation", "editable HTML", "interactive deck"). Never silently downgrade image → html when rendering fails.

## Acceptance criteria

A deck is **done** when all of the following hold. If any fail, the task is not complete.

**Directory & plan**

- `deck_plan.md` states mode, audience, thesis, and a slide list where each entry has one claim and a visual role.
- `speaker_notes.md` exists; notes add spoken context, they do not repeat slide text verbatim. Create or substantially rewrite them against the [speaker-notes spoken-delivery contract](speaker_notes.md).
- A validation note records what was previewed and what remains unresolved.
- If a distribution PDF is requested for an image deck, it is built with `scripts/presentation-skill export-pdf` (compat gate passed, link count matches the overlay plan) — not by printing from a browser.

**Preview**

- `start-server.py` serves `index.html` without errors; arrow-key navigation works through every slide.
- If port 8080 or 8000 is occupied, use another port (e.g. 8765).

**Image mode**

- `visual_guideline.md` defines shared style; `outline_visual.md` has one `#### Slide N:` block per slide with **exact** on-slide text in prompts (not "make it look professional").
- Prompts distinguish **visible copy** from **design instructions**. Internal constraints such as "do not show performance numbers" or "use public data only" stay in the prompt as rules, never as text the model may paint onto the slide.
- Every `data-background` path in `index.html` resolves to a file under `generated_slides/`.
- Logos, QR codes, screenshots, and tables use real assets under `imgs/` — never ask the image model to invent them.
- On-slide text is legible; garbled text is a failure (simplify copy, re-render, or overlay exact text in HTML/CSS).

**HTML mode**

- One module per slide under `js/slides/`; each exports `render`, `initialize`, `cleanup` per `js/slideModule.js`.
- Slide IDs in `index.html` match the `slideIds` array; leaving a slide cleans up timers, listeners, charts, and WebGL.

**Cross-mode awareness**

- Before editing, read the scaffold's root files (active mode) and skim `examples/<other-mode>/` so you know which paradigm applies.

## Available resources

**Scaffold (start here for a new deck)**

```bash
bash scripts/presentation-skill "Topic" --mode image --output deck_work
bash scripts/presentation-skill "Topic" --request "HTML only" --output deck_work
```

**PDF export (image decks — the default way to produce the distribution PDF)**

```bash
bash scripts/presentation-skill export-pdf deck_work --check-only   # compatibility gate only
bash scripts/presentation-skill export-pdf deck_work --output deck_work/handout/slides.pdf
```

Builds the PDF straight from the slide images (lossless, no browser printing) and embeds every `overlay-data` hotzone as a PDF link annotation at the same rect + padding as the HTML overlay, so PDF and HTML click identically. The compatibility gate requires every section to be background-image + notes only and fails loudly otherwise — if it reports INCOMPATIBLE, fix the deck or fall back to a manual export; never ship a silently lossy PDF. Requires the `[pdf]` extra (img2pdf + pypdf).

After init, read `deck_work/README.md`. Active mode is at deck root; the other mode is under `examples/`.

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

When a slide needs navbar + logo + chart (or QR), list all assets in `outline_visual.md`; the generator stacks them for gpt-image-2 and you describe top-to-bottom mapping in the prompt.

**Mode → root artifacts**

| Mode | Root artifacts |
|------|----------------|
| image | `outline_visual.md`, `visual_guideline.md`, `generated_slides/`, `tools/`, image `index.html` |
| html | `index.html`, `js/slides/*.js`, `js/slideModule.js` |

## Methodology (suggestions, not mandatory order)

- One claim per slide; prefer concrete statements over topic labels like "Architecture".
- For direct-read scripts or substantial speaker-note revisions, load [speaker_notes.md](speaker_notes.md). It defines the breath test, transition handoffs, factual-fidelity gate, and long-deck batch review.
- Image decks: unify style through `visual_guideline.md` + shared style reference assets; render only after outline text is locked.
- Text-heavy image slides: keep title regions wide, cap visible labels, and explicitly require normal-width typography. Long text in a narrow column often makes image models fake a condensed font or horizontally squeeze letters.
- HTML decks: keep slide state local; treat `examples/html/js/slides/title.js` as the module contract reference.
- Prefer the workspace image-generation skill when available.
- Image decks that show URLs/QRs or embed live artifacts: add a clickable HTML overlay layer per [docs/clickable_overlays.md](../docs/clickable_overlays.md) — prompt the zone, measure the rendered element's bbox by vision, inject padded `<a>`/iframe hotzones, verify with a draw-back check.

## Known traps

| Trap | How it shows up | What to do |
|------|-----------------|------------|
| Wrong install path | Agent reads a stale `.agents/skills/` or injected path that does not exist | Follow the installing workspace's skill index / `WORKSPACE.md`. Canonical repo skill: `skills/skill_presentation.md` in the `presentation_skill` package. |
| Treating Python helpers as an AI planner | Expecting `deck_plan.py` or CLI to generate slide content | Python only scaffolds directories and encodes validation rules. The agent writes `deck_plan.md`, outlines, and modules. |
| Silent mode downgrade | Image API fails → agent switches to HTML without asking | Stop; state the blocker; keep source artifacts complete; switch modes only if the user allows. |
| Model-invented text | QR codes that don't scan, alien glyphs, hallucinated logos | Put exact pixels in `imgs/` and inject via outline Asset sections; specify exact readable copy in prompts. |
| Internal constraints painted onto slides | Prompt says "no private numbers" or "public data only" and the rendered slide visibly includes that caveat | Separate rules from visible copy. Phrase constraints as "Do not render any text about X" and enumerate the exact visible headings/labels the model may draw. |
| Horizontally squeezed typography | Long titles or card text look narrow/condensed, especially inside a fixed left column | Shorten the visible phrase, give the title full width, and add: "Use normal-width Inter or Helvetica-style sans-serif, not condensed. Do not horizontally scale or compress letters; reduce font size or wrap at word boundaries." If it persists, move exact text to an HTML/CSS overlay. |
| Mixing paradigms on one slide | Editing JS modules for a slide that should be a rendered JPG (or vice versa) | Pick one mode per slide; use html mode only for slides that need live interaction. |
| Skipping examples | New slides drift from the scaffold contract | Read root scaffold + `examples/` before writing; adapt from those patterns. |
| Preview without server | Opening `index.html` as `file://` breaks modules/CDN | Use `start-server.py`; pick a free port if defaults are taken. |
| English/Mixed Prompts in Chinese Decks | Mixing English and Chinese in MJ/DALL-E prompts for Chinese slides | Use **100% pure Chinese prompts** (excluding standard CLI parameters like `--ar 16:9`). Any English keywords (e.g. "vs", "chart", "mockup") trigger the image model to draw garbled, meaningless English glyphs on the slide background. |
| Bracketed English Translations | "中文 (英文)" or "中文（英文）" bracketed pairs in text overlay or notes | **Never** use bracketed translations (e.g. "事实包 (Information Pack)"). They serve no purpose for Chinese audiences and dramatically increase visual noise. |
| Non-Visual Transition Logical Flow | Adding logic comments in outline but slide visual remains disjointed | Logic transitions must be **visualized**. Incorporate a consistent **Top Navigation Bar / Flow Indicator** in the prompt (instructing the model to paint it and highlight the active step) and in the text overlay. |
| Abstract or Vague Chart Prompts | Asking the model to "draw a radar chart of AI sychophancy/quality metrics" | Specify the **exact dimensions** (e.g. five dimensions: "AI腔词汇比率", "空洞无事实比率") and exact numbers/comparison pairs in the prompt. Do not leave abstractions for the image model to invent. |
| PYTHONPATH Missing for Generator | `generate_slides.py` fails with ModuleNotFoundError: No module named 'tools' | Prepend `PYTHONPATH=.` when running generation scripts from local slide directories to fix Python module paths. |
| Multi-image asset limit (gpt-image-2) | Listing navbar + logo + QR (or chart + style ref) under `Asset` triggers `gpt-image-2 currently supports at most one input image` | **Do not drop assets.** Keep every needed pixel reference in the outline `Asset` list. `tools/generate_slides.py` auto-stacks multiple assets vertically with Pillow into `generated_slides/stacked_assets_slide_N.png` and passes that single composite to the model. **Prompt must name the stack order** — e.g. 「参考叠加 Asset 自上而下依次为：导航条样式、Logo、二维码」 — so the model maps each region correctly. Asset order in the outline = top-to-bottom stack order. |
| Hallucinated Quantitative Chart Details | asking the image model to draw exact numerical charts (bar charts, line graphs) | Always pre-plot quantitative charts using Python + Matplotlib to generate a precise PNG image, use it as the single `Asset`, and guide the image model to replicate its content and layout. |
| Painted links that don't click | A URL pill or QR caption rendered into the slide image; audience receives the HTML deck and nothing is clickable, or overlay coords copied from the prompt miss the element by ~5% | Add an overlay layer per [docs/clickable_overlays.md](../docs/clickable_overlays.md): coordinates come from post-generation vision measurement (not from the prompt), hotzones get 1.5% padding, and each overlay is verified with a Pillow draw-back check. |
| Printed-PDF link 404s / tiny pages | `?print-pdf` rewrites overlay links to the *visible pill text* (so `x.com/a` 404s when href is `x.com/a.html`), and un-sized Reveal prints each slide as a tiny centered box | Don't print from the browser at all: `scripts/presentation-skill export-pdf <deck>` builds the PDF from the images and embeds overlay links as real PDF annotations. Browser printing is a last resort only when the compat gate reports the deck isn't a pure image deck. |
| Dense text exhibits corrupted on hi-res re-render | A screenshot asset full of numbers (a report, a table) passes QC at draft size, then the 4K batch redraws it with mangled digits ("$25.11" → "$2.11") — and re-rolls keep mangling different spots | Stop re-rolling. Composite deterministically: locate the exhibit frame on the generated slide (detect the border lines programmatically), re-render the true source (e.g. headless-Chrome screenshot of the styled document, width-tuned to the frame's aspect), and paste the real pixels inside the frame with Pillow. The model draws the frame; the content stays ground truth. |

## Additional resources

- Detailed contracts, scaffold layout, installation: [reference.md](reference.md)
- Direct-read scripts and spoken delivery: [speaker_notes.md](speaker_notes.md)
- Clickable links / live-artifact embeds on image slides: [docs/clickable_overlays.md](../docs/clickable_overlays.md)
