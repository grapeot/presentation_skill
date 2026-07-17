# Clickable Overlays for Image-Mode Decks

Image-mode decks render each slide as a full-bleed generated image behind a Reveal.js `<section>`. Anything the model paints — a URL pill, a "handout" button, a QR caption — is pixels, not hypertext. This doc is the recipe for adding a real, clickable HTML layer on top of the image, so links survive in the distributed HTML deck and live artifacts can be embedded without leaving the deck.

Validated 2026-07 with a two-stage experiment (gpt-image-2, 1536x864, two samples per prompt); findings are inlined below.

## When to use

- A slide shows a URL, QR, or "read more" affordance that the audience will receive as an HTML deck and expect to click.
- A slide should embed a live local artifact (an interactive chart, a demo page) inside the deck instead of switching windows.

Skip it for decks distributed only as video or presented live with no handout — painted pixels are enough there.

## How placement works: prompt the zone, measure the pixels

Two experimental facts drive the design:

1. **Prompted placement is region-accurate, not pixel-accurate.** Asking gpt-image-2 for "a pill button, horizontally centered, vertical center at about 88% of slide height" landed the element in the requested zone in both samples, but with ±5% height variance across samples. Text inside the elements rendered exactly (including hyphenated URLs) in all samples.
2. **Vision measurement closes the gap in one pass.** After generation, the agent reads the image, estimates the element's normalized bounding box, and verifies by drawing the box back onto a copy (Pillow) and reading the result. Measured error was ~1-2% of width/height — smaller than the hotzone padding you should add anyway.

So the pipeline is:

```
prompt names the zone  →  generate  →  agent reads image, records bbox
→  overlays.json  →  inject <a> layer  →  draw-back verification
```

No human clicking, no coordinate guessing in prompts, no CI: the draw-back check is a deterministic agent step.

## overlays.json

One file at deck root. Keys are slide `<section>` ids; values are overlay items with normalized rects (fractions of slide width/height, origin top-left).

```json
{
  "slide-07": [
    { "type": "link", "href": "https://yage.ai/stop-using-chatgpt.html",
      "rect": [0.28, 0.81, 0.75, 0.91], "label": "yage.ai/stop-using-chatgpt" },
    { "type": "link", "href": "https://example.com/handout",
      "rect": [0.85, 0.89, 0.97, 0.95], "label": "Handout" }
  ],
  "slide-09": [
    { "type": "iframe", "src": "assets/mu_events.html", "rect": [0.05, 0.12, 0.95, 0.92] }
  ]
}
```

Conventions:

- `rect` is the measured bbox of the painted element; the injector pads it by 1.5% per side to absorb measurement error.
- Default overlays are invisible hotzones over the painted element (the image already looks like a button). Set `"visible": true` to render a styled pill instead — useful when the slide image deliberately leaves an empty zone.
- `label` is for the agent's own bookkeeping and accessibility (`aria-label`); it is not rendered unless `visible`.
- `href` may be an `http(s)` URL or a safe relative link such as `../handout/index.html`. Relative links remain relative in both the HTML deck and exported PDF, so place the PDF beside `index.html` when they should resolve to the same local targets.

## Injection snippet

Append once to the image-mode `index.html` (after the Reveal initialization):

```html
<style>
  .reveal section .img-overlay {
    position: absolute; display: block; z-index: 10;
    /* debug: uncomment to see hotzones while verifying */
    /* outline: 2px dashed rgba(255,80,80,.7); */
  }
  .reveal section .img-overlay.visible {
    background: rgba(80,160,255,.85); color: #fff; border-radius: 999px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.6em; text-decoration: none;
  }
  .reveal section .img-overlay-frame {
    position: absolute; z-index: 10; border: 0; background: #111;
  }
</style>
<script id="overlay-data" type="application/json">
  /* paste overlays.json content here, or fetch it if serving over http */
</script>
<script>
  (function () {
    var data = JSON.parse(document.getElementById("overlay-data").textContent);
    var PAD = 0.015;
    Object.keys(data).forEach(function (id) {
      var sec = document.getElementById(id);
      if (!sec) return;
      data[id].forEach(function (it) {
        var pad = it.pad != null ? it.pad : PAD;
        var r = it.rect;
        var el;
        if (it.type === "iframe") {
          el = document.createElement("iframe");
          el.src = it.src;
          el.className = "img-overlay-frame";
          pad = 0;
        } else {
          el = document.createElement("a");
          el.href = it.href;
          el.target = "_blank";
          el.rel = "noopener";
          el.className = "img-overlay" + (it.visible ? " visible" : "");
          el.setAttribute("aria-label", it.label || it.href);
          if (it.visible) el.textContent = it.label || it.href;
        }
        el.style.left = ((r[0] - pad) * 100) + "%";
        el.style.top = ((r[1] - pad) * 100) + "%";
        el.style.width = ((r[2] - r[0] + 2 * pad) * 100) + "%";
        el.style.height = ((r[3] - r[1] + 2 * pad) * 100) + "%";
        sec.appendChild(el);
      });
    });
  })();
</script>
```

Notes:

- Reveal slides have fixed logical dimensions, so percentage positioning against the `<section>` tracks the background image at every window size.
- Inline the JSON for `file://` double-click distribution; `fetch("overlays.json")` only works over http.
- The iframe variant expects the embedded artifact to be a single self-contained HTML file placed under the deck directory (e.g. `assets/`).

## Workflow for the agent

1. In `outline_visual.md`, describe link affordances with a zone, not coordinates ("light-blue pill, horizontally centered, vertical center around 88% height, exact text '...'"). The exact on-slide text must equal the href's visible form (including any `.html`) — this is what a printed PDF uses as the link target.
2. After rendering, Read each affected slide image and record the painted element's normalized bbox into `overlays.json`.
3. Verify: draw each rect onto a copy of the image with Pillow, Read the copy, confirm the box hugs the element. Re-measure any miss (one pass sufficed in testing).
4. Inject the snippet, serve the deck, and confirm each overlay opens the right target (Playwright click or manual spot-check).
5. Record the verification in the deck's validation note.

## Export caveats

Two distribution formats, two different behaviors — pick deliberately:

**HTML deck (`?print-pdf` off)** — all overlays clickable. Prefer this as the take-home format when links matter.

**Browser `?print-pdf` → Save as PDF** — Reveal *does* carry the overlay `<a>` elements into the PDF, so links survive. But this is where a subtle bug bites: **the printed PDF turns the overlay's visible text into the link, not its `href`.** If the painted pill reads `example.com/page` but the `href` is `example.com/page.html`, the browser prints a link pointing at `example.com/page` — a 404. The `href` is correct in the live deck (clicking works there); only the print step rewrites it from the visible text.

  - **Fix**: make the overlay's visible text (both the painted pill text in `outline_visual.md` and the `label` in `overlays.json`) **character-for-character equal to the `href`'s user-visible form**, including any `.html` suffix. If the link is `https://x.com/a.html`, the pill must read `x.com/a.html`, not `x.com/a`.
  - Also set Reveal's logical size to the slide size (`width: 1920, height: 1080, margin: 0`) or `?print-pdf` renders each page as a tiny centered box on the sheet regardless of the print dialog's scale setting.

**Pixel-perfect PDF via img2pdf (recommended for handouts)** — bypass the browser entirely. Concatenate the rendered slide JPGs straight into a PDF:

```python
import img2pdf, glob
files = sorted(glob.glob('generated_slides_4k/slide_*_0.jpg'))
with open('handout/slides.pdf', 'wb') as f:
    f.write(img2pdf.convert(files))
```

This is lossless (no browser re-rasterization), one page per slide, exact 16:9, and immune to the print-scale and link-rewrite bugs above. The tradeoff: image-only PDF has **no clickable links** — so the on-slide pill text must be a readable URL the reader can type or scan. Since the fix above already forces the pill text to equal the URL, this is free. Document in the handout README that PDF links are printed, not clickable.

## Known traps

| Trap | How it shows up | What to do |
|------|-----------------|------------|
| Treating prompted position as exact | Overlay drawn from the prompt's "88%" lands off the pill that actually rendered at 83% | Coordinates always come from post-generation measurement, never from the prompt |
| Zero-padding hotzones | Link works in testing, misses by a few pixels for the audience | Keep the 1.5% default padding; painted pills tolerate a slightly larger invisible hotzone |
| Styling the whole deck from the overlay CSS | Global selectors leak into Reveal chrome | Scope every rule under `.reveal section .img-overlay*` |
| fetch() for local decks | Overlays silently absent when the deck is opened via `file://` | Inline the JSON into the `overlay-data` script tag |
| Overlay text ≠ href in printed PDF | Live deck link works, but the `?print-pdf` PDF points at the visible text and 404s (e.g. pill says `x.com/a`, href is `x.com/a.html`) | Make the painted pill text and `overlays.json` `label` exactly equal the href's visible form, `.html` and all |
| Tiny centered pages on `?print-pdf` | Every PDF page is a small box mid-sheet, scale slider does nothing | Set Reveal `width: 1920, height: 1080, margin: 0`; or skip the browser and build the PDF with img2pdf from the slide images |
