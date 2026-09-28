# Generated Assets in HTML Decks

Generated assets are local visual components that live inside a DOM-composed slide. In practice, they work best as textless icons, conceptual diagrams, and illustrations that help distinguish peers or explain a mechanism much faster than prose.

## Boundary

Use generated assets for visual meaning that can comfortably tolerate probabilistic pixels. On the other hand, you must use exact local assets or deterministic rendering for logos, QR codes, screenshots, tables, code, quantitative charts, and any text or number that must be correct.

Keep in mind that image generation belongs to the installing workspace. This repo supplies the presentation contract and deterministic post-processing only; it does not call a provider API.

## Acceptance criteria

- Every asset must have an explicit cognitive role documented in `deck_plan.md`; wanting to “fill empty space” is never enough.
- A related asset set must share the same shape language, line weight, palette, density, and perspective.
- Raster assets must have transparent backgrounds, tight bounds, and show no dark box or halo on the actual slide surfaces.
- Assets in peer cards must align cleanly through one stable container such as `.card-visual`.
- Generated pixels must contain no required copy, data, logo, QR code, or exact chart.
- Informative images must provide useful `alt` text, whereas decorative images use empty `alt`.
- The slide must still communicate its claim even when the image fails to load.

## Visual grammar

Make sure you lock a deck-level grammar before generating a set. That means defining 2D versus 3D, stroke or fill, target colors, forbidden gradients/shadows, background assumption, and expected aspect ratio. When prompting, prompt for one semantic object or relationship per asset; do not ask the model to compose the whole slide.

Flat line assets often integrate particularly well because they can be recolored and made transparent deterministically. Simply generate them against a simple dark or light background with strong foreground separation, and then normalize them:

```bash
presentation-skill prepare-asset raw-icon.png imgs/icon.png \
  --target-color '#D6A24B' \
  --background dark \
  --low 40 --high 100 \
  --padding 24 --crop square
```

Be sure to tune the thresholds from your actual source. The defaults reflect a real dark-background, bright-line workflow, so they are not universal constants. In terms of cropping, `tight` preserves the content aspect ratio, `square` centers the tight crop in a transparent square, and `none` keeps the original canvas.

## Known failures

| Failure | Response |
|---|---|
| Icon has a visible background rectangle | Extract the alpha channel, inspect the result on every real card surface, and adjust your thresholds. |
| Thin antialiased lines acquire a dark halo | Raise the background-side threshold, or regenerate the image with stronger separation between foreground and background. |
| Cards jump because assets have different whitespace | Apply a tight-crop first, then normalize the placement through a fixed-height `.card-visual` container. |
| A generated diagram invents labels or numbers | Remove the text from the graphic and put exact labels in the DOM, or draw the entire diagram deterministically. |
| Assets look individually good but unrelated | Regenerate them together as a locked set against one visual grammar and a shared style reference. |

## Plates for canvas decks

A canvas deck gets much of its expensive, bespoke feel from a set of textless illustration plates that share one unified style. On our reference deck, for example, we used 19th-century steel engravings, rendered as ink on paper with one subject each, printed directly onto the page.

**Choose the metaphor, not the topic.** Pick an object the audience recognises without a caption and that carries the argument: a card catalogue for retrieval (representing the old problem underneath), scaffolding for a temporary structure, a telephone switchboard for protocols, a stone tablet for knowledge baked into weights, or a split geode for "you have to open it to see inside".

**Lock the style on one plate first.** Write one style paragraph specifying the medium, line technique, paper, and explicit constraints ("no text, no letters, no numbers, no border, isolated subject, wide margin") and render a single plate. Once it is right, you can render the rest in parallel with that same paragraph (typically 4–6 at a time, keeping in mind each call can take minutes). Since long prompts tend to break `xargs -I`, use a small script with a thread pool instead.

**Print, don't paste.** You need to convert every plate to ink on transparent. That's because blend modes do not reach the page through a transformed world layer, so an untreated plate will show up as an unsightly white rectangle.

```bash
presentation-skill prepare-asset raw/plate.png imgs/plate.png \
  --target-color '#1b2130' --background light --low 40 --high 248 --crop tight --padding 20
```

If the paper tone varies between renders, first divide each image by the median colour of its border so the paper becomes exactly white. Then compress the files (WebP works well here; keep the long side around 1000 px).

**Check the set on one contact sheet** before you start building with it. Anything tinted, glossy, carrying text, or rendered in a different technique gets regenerated from the same paragraph.

**3D is optional.** Going through a Blender render is justified only when a claim genuinely needs real light, parallax or a physical object turning. On the reference deck, the engraving set carried the entire look without it.
