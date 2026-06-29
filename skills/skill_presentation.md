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
- `speaker_notes.md` exists; notes add spoken context, they do not repeat slide text verbatim.
- A validation note records what was previewed and what remains unresolved.

**Preview**

- `start-server.py` serves `index.html` without errors; arrow-key navigation works through every slide.
- If port 8080 or 8000 is occupied, use another port (e.g. 8765).

**Image mode**

- `visual_guideline.md` defines shared style; `outline_visual.md` has one `#### Slide N:` block per slide with **exact** on-slide text in prompts (not "make it look professional").
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

After init, read `deck_work/README.md`. Active mode is at deck root; the other mode is under `examples/`.

**Preview**

```bash
cd deck_work
uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python start-server.py --port 8765 --no-browser
```

**Image rendering** (inside scaffolded deck, uses workspace credentials via `.env`)

```bash
python tools/generate_slides.py --outline outline_visual.md
```

**Mode → root artifacts**

| Mode | Root artifacts |
|------|----------------|
| image | `outline_visual.md`, `visual_guideline.md`, `generated_slides/`, `tools/`, image `index.html` |
| html | `index.html`, `js/slides/*.js`, `js/slideModule.js` |

## Methodology (suggestions, not mandatory order)

- One claim per slide; prefer concrete statements over topic labels like "Architecture".
- Image decks: unify style through `visual_guideline.md` + shared style reference assets; render only after outline text is locked.
- HTML decks: keep slide state local; treat `examples/html/js/slides/title.js` as the module contract reference.
- Prefer the workspace image-generation skill when available.

## Known traps

| Trap | How it shows up | What to do |
|------|-----------------|------------|
| Wrong install path | Agent reads a stale `.agents/skills/` or injected path that does not exist | Follow the installing workspace's skill index / `WORKSPACE.md`. Canonical repo skill: `skills/skill_presentation.md` in the `presentation_skill` package. |
| Treating Python helpers as an AI planner | Expecting `deck_plan.py` or CLI to generate slide content | Python only scaffolds directories and encodes validation rules. The agent writes `deck_plan.md`, outlines, and modules. |
| Silent mode downgrade | Image API fails → agent switches to HTML without asking | Stop; state the blocker; keep source artifacts complete; switch modes only if the user allows. |
| Model-invented text | QR codes that don't scan, alien glyphs, hallucinated logos | Put exact pixels in `imgs/` and inject via outline Asset sections; specify exact readable copy in prompts. |
| Mixing paradigms on one slide | Editing JS modules for a slide that should be a rendered JPG (or vice versa) | Pick one mode per slide; use html mode only for slides that need live interaction. |
| Skipping examples | New slides drift from the scaffold contract | Read root scaffold + `examples/` before writing; adapt from those patterns. |
| Preview without server | Opening `index.html` as `file://` breaks modules/CDN | Use `start-server.py`; pick a free port if defaults are taken. |
| English/Mixed Prompts in Chinese Decks | Mixing English and Chinese in MJ/DALL-E prompts for Chinese slides | Use **100% pure Chinese prompts** (excluding standard CLI parameters like `--ar 16:9`). Any English keywords (e.g. "vs", "chart", "mockup") trigger the image model to draw garbled, meaningless English glyphs on the slide background. |
| Bracketed English Translations | "中文 (英文)" or "中文（英文）" bracketed pairs in text overlay or notes | **Never** use bracketed translations (e.g. "事实包 (Information Pack)"). They serve no purpose for Chinese audiences and dramatically increase visual noise. |
| Non-Visual Transition Logical Flow | Adding logic comments in outline but slide visual remains disjointed | Logic transitions must be **visualized**. Incorporate a consistent **Top Navigation Bar / Flow Indicator** in the prompt (instructing the model to paint it and highlight the active step) and in the text overlay. |
| Abstract or Vague Chart Prompts | Asking the model to "draw a radar chart of AI sychophancy/quality metrics" | Specify the **exact dimensions** (e.g. five dimensions: "AI腔词汇比率", "空洞无事实比率") and exact numbers/comparison pairs in the prompt. Do not leave abstractions for the image model to invent. |
| PYTHONPATH Missing for Generator | `generate_slides.py` fails with ModuleNotFoundError: No module named 'tools' | Prepend `PYTHONPATH=.` when running generation scripts from local slide directories to fix Python module paths. |

## Additional resources

- Detailed contracts, scaffold layout, installation: [reference.md](reference.md)
