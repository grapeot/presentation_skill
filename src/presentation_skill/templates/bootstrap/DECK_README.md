# Presentation Deck Workspace

This directory was initialized by `presentation-skill`. The **active deck** lives at the repo root (`index.html`). Cross-mode reference examples live under `examples/`.

## Active mode

Check `deck_plan.md` for the selected rendering mode (`image` or `reveal`) and its independent asset policy (`none`, `generated`, `exact`, or `mixed`).

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

## Reveal mode workflow

1. Keep static slide markup in `js/deck.js` and exact copy/layout in the DOM.
2. Use `js/slides/` modules only for slides with listeners, timers, charts, or WebGL; each exports `initialize` and `cleanup`.
3. Put exact and generated local assets under `imgs/`; align peer visuals through a shared `.card-visual` container.
4. Use `presentation-skill prepare-asset` to normalize generated line art when transparent PNG output is needed.
5. Preview with `start-server.py` as above.

See `examples/html/` for the Reveal reference deck. The directory keeps its legacy physical name for compatibility.

## Before changing slides

Read the reference example for your active mode **and** skim the other mode under `examples/` so you know when to switch paradigms.
