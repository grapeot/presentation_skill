# Presentation Deck Workspace

This directory was initialized by `presentation-skill`. The **active deck** lives at the repo root (`index.html`). Cross-mode reference examples live under `examples/`.

## Active mode

Check `deck_plan.md` for the selected rendering mode (`image` or `html`) and its independent asset policy (`none`, `generated`, `exact`, or `mixed`).

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

See `examples/image/` for a complete reference deck (same layout as the root when mode is image). The HTML canvas reference deck is under `examples/html/`.

## HTML mode workflow (canvas)

1. `npm install && npm run vendor` once, so Reveal.js and the fonts are local and the deck runs offline.
2. Plan the sheet in `deck_plan.md` and `visual_guideline.md`: one claim per slide, what moves on each click.
3. Edit the slide table in `js/deck.js` and the frames in `tools/build_index.py`, then run `python3 tools/build_index.py`.
4. Write the copy through the writer packet in `copy/` (templates included), then run `python3 tools/copy_to_js.py`.
5. Verify with `python3 tools/shoot.py --out verification/round1` and run a critic round on the contact sheets.
6. Preview with `start-server.py`; press S for the speaker view. Pages reload on their own when you save (the slide and step are kept), so you can edit notes with the speaker view open.

See `examples/html/` for the reference canvas deck and the skill's `html_decks.md` for the full contract.

## Before changing slides

Read the reference example for your active mode **and** skim the other mode under `examples/` so you know when to switch paradigms.
