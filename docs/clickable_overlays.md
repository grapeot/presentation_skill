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

1. In `outline_visual.md`, describe link affordances with a zone, not coordinates ("light-blue pill, horizontally centered, vertical center around 88% height, exact text '...'"). Exact on-slide text in the prompt, as always.
2. After rendering, Read each affected slide image and record the painted element's normalized bbox into `overlays.json`.
3. Verify: draw each rect onto a copy of the image with Pillow, Read the copy, confirm the box hugs the element. Re-measure any miss (one pass sufficed in testing).
4. Inject the snippet, serve the deck, and confirm each overlay opens the right target (Playwright click or manual spot-check).
5. Record the verification in the deck's validation note.

## Export caveats

- The distributed HTML deck keeps all overlays working — prefer it as the take-home format.
- PDF export drops the overlay layer. If a PDF is required, add a final "All links" appendix slide (plain text URLs / QR) so nothing is lost.

## Known traps

| Trap | How it shows up | What to do |
|------|-----------------|------------|
| Treating prompted position as exact | Overlay drawn from the prompt's "88%" lands off the pill that actually rendered at 83% | Coordinates always come from post-generation measurement, never from the prompt |
| Zero-padding hotzones | Link works in testing, misses by a few pixels for the audience | Keep the 1.5% default padding; painted pills tolerate a slightly larger invisible hotzone |
| Styling the whole deck from the overlay CSS | Global selectors leak into Reveal chrome | Scope every rule under `.reveal section .img-overlay*` |
| fetch() for local decks | Overlays silently absent when the deck is opened via `file://` | Inline the JSON into the `overlay-data` script tag |
