# Presentation Deck Workspace

This directory was initialized by `presentation-skill`. The **active deck** lives at the repo root (`index.html`). Cross-mode reference examples live under `examples/`.

## Active mode

Check `deck_plan.md` for the selected mode (`image` or `html`).

## Preview locally

```bash
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python start-server.py --port 8765 --no-browser
```

Open `http://localhost:8765`. Use a port other than 8000 if that port is occupied.

## Image mode workflow

1. Edit `outline_visual.md` (per-slide scenes) and `visual_guideline.md` (shared style).
2. Place exact assets under `imgs/` when a slide needs logos, QR codes, or screenshots.
3. Render slides: `python tools/generate_slides.py --outline outline_visual.md`
4. Images land in `generated_slides/`; `index.html` references them via Reveal.js `data-background`.
5. Add speaker notes in `<aside class="notes">` inside each `<section>` in `index.html`.

See `examples/image/` for a complete reference deck (same layout as the root when mode is image).

## HTML module mode workflow

1. Add or edit one file per slide under `js/slides/`.
2. Register slide IDs in `index.html` (`slideIds` array and empty `<section id="...">` placeholders).
3. Each module exports `render`, `initialize`, and `cleanup` (see `js/slideModule.js` and `examples/html/js/slides/title.js`).
4. Preview with `start-server.py` as above.

See `examples/html/` for a complete reference deck with Chart.js, Three.js, and progressive reveals.

## Before changing slides

Read the reference example for your active mode **and** skim the other mode under `examples/` so you know when to switch paradigms.
