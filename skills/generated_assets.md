# Generated Assets in Reveal Decks

Generated assets are local visual components inside a DOM-composed slide. They work best as textless icons, conceptual diagrams, and illustrations that distinguish peers or explain a mechanism faster than prose.

## Boundary

Use generated assets for visual meaning that can tolerate probabilistic pixels. Use exact local assets or deterministic rendering for logos, QR codes, screenshots, tables, code, quantitative charts, and any text or number that must be correct.

Image generation belongs to the installing workspace. This repo supplies the presentation contract and deterministic post-processing only; it does not call a provider API.

## Acceptance criteria

- Every asset has an explicit cognitive role in `deck_plan.md`; “fill empty space” is not enough.
- A related asset set shares shape language, line weight, palette, density, and perspective.
- Raster assets have transparent backgrounds, tight bounds, and no dark box or halo on the actual slide surfaces.
- Assets in peer cards align through one stable container such as `.card-visual`.
- Generated pixels contain no required copy, data, logo, QR code, or exact chart.
- Informative images have useful `alt`; decorative images use empty `alt`.
- The slide still communicates its claim when the image fails to load.

## Visual grammar

Lock a deck-level grammar before generating a set. Define 2D versus 3D, stroke or fill, target colors, forbidden gradients/shadows, background assumption, and expected aspect ratio. Prompt for one semantic object or relationship per asset; do not ask the model to compose the whole slide.

Flat line assets often integrate well because they can be recolored and made transparent deterministically. Generate against a simple dark or light background with strong foreground separation, then normalize them:

```bash
presentation-skill prepare-asset raw-icon.png imgs/icon.png \
  --target-color '#D6A24B' \
  --background dark \
  --low 40 --high 100 \
  --padding 24 --crop square
```

Tune thresholds from the actual source. The defaults reflect a real dark-background, bright-line workflow; they are not universal constants. `tight` preserves the content aspect ratio, `square` centers the tight crop in a transparent square, and `none` keeps the original canvas.

## Known failures

| Failure | Response |
|---|---|
| Icon has a visible background rectangle | Extract alpha, inspect on every real card surface, and adjust thresholds. |
| Thin antialiased lines acquire a dark halo | Raise the background-side threshold or regenerate with stronger foreground/background separation. |
| Cards jump because assets have different whitespace | Tight-crop, then normalize through a fixed-height `.card-visual` container. |
| A generated diagram invents labels or numbers | Remove its text and put exact labels in the DOM, or draw the entire diagram deterministically. |
| Assets look individually good but unrelated | Regenerate as a locked set against one visual grammar and shared reference. |

## Plates for canvas decks

A canvas deck gets much of its expensive feel from a set of textless illustration plates that share one style.
On the reference deck: 19th-century steel engravings, ink on paper, one subject each, printed onto the page.

**Choose the metaphor, not the topic.** Pick an object the audience recognises without a caption and that
carries the argument: a card catalogue for retrieval (the old problem underneath), scaffolding for a temporary
structure, a telephone switchboard for protocols, a stone tablet for knowledge baked into weights, a split geode
for "you have to open it to see inside".

**Lock the style on one plate first.** Write one style paragraph (medium, line technique, paper, "no text, no
letters, no numbers, no border, isolated subject, wide margin") and render a single plate. Once it is right,
render the rest in parallel with the same paragraph (4–6 at a time; each call can take minutes). Long prompts
break `xargs -I`; use a small script with a thread pool instead.

**Print, don't paste.** Convert every plate to ink on transparent. Blend modes do not reach the page through a
transformed world layer, so an untreated plate shows up as a white rectangle.

```bash
presentation-skill prepare-asset raw/plate.png imgs/plate.png \
  --target-color '#1b2130' --background light --low 40 --high 248 --crop tight --padding 20
```

If the paper tone varies between renders, first divide each image by the median colour of its border so the
paper becomes exactly white. Then compress (WebP works well; keep the long side around 1000 px).

**Check the set on one contact sheet** before building with it. Anything tinted, glossy, carrying text, or in a
different technique gets regenerated from the same paragraph.

**3D is optional.** A Blender render is justified only when a claim needs real light, parallax or a physical
object turning. On the reference deck, the engraving set carried the look without it.
