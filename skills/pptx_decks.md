# Editable PPTX decks

Use this mode when the deck is a working file rather than a finished show: a co-author will open it in PowerPoint or Google Slides, rewrite sentences, swap a figure, and present from there. The image mode bakes text into pictures, and the HTML canvas mode keeps text in the DOM; neither leaves an editable slide after the handoff.

## The two layers

Each slide is split into a picture layer and a text layer.

The picture layer holds everything nobody will edit word by word: illustrations, diagrams drawn as SVG, photos, screenshots, figures from papers. Export SVG diagrams to PNG at twice the displayed size before placing them. Google Slides does not import SVG, and an SVG embedded in a PPTX is rasterized or dropped on import.

The text layer holds every readable word: the title, labels, captions, quotes, callouts on a diagram, the numbers a speaker may want to update. These are native text boxes and rounded-rectangle bubbles. A diagram whose labels may change gets drawn as an unlabeled plate with text boxes placed over it. Lines that should stay movable, such as a timeline path, can be native freeform lines.

Keep the copy in Markdown until it is approved, then move it into the spec. The spec is the source of truth until handoff; after the co-author starts editing in Google Slides, their file is.

## Spec format

Start from `presentation-skill "Topic" --mode pptx --output deck`, which writes a one-slide `slides.json`, a `plates/` folder and a README. `build-pptx` reads one JSON file. Image paths resolve relative to it. Coordinates are inches on a 13.333 × 7.5 canvas (16:9) unless `canvas` says otherwise.

```json
{
  "theme": {
    "font": "Arial",
    "text_color": "#1F2A36",
    "muted_color": "#5B6670",
    "accent_color": "#B3261E",
    "title_size": 30,
    "body_size": 20,
    "title_bar": {"color": "#0F4D92", "height": 1.1},
    "title_color": "#FFFFFF"
  },
  "slides": [
    {
      "title": "Results: the effect grows with temperature",
      "elements": [
        {"type": "image", "path": "plates/results.png", "box": [0.6, 1.4, 7.4, 5.2]},
        {"type": "bubble", "box": [8.3, 1.6, 4.4, 1.1], "line": "#9AA5B1",
         "text": "\"Does the trend survive the control sample?\""},
        {"type": "text", "style": "caption", "box": [0.6, 6.7, 7.4, 0.5],
         "text": "Each point is one sample; the line is a guide to the eye."},
        {"type": "line", "points": [[0.8, 6.0], [3.0, 4.8], [5.2, 3.6], [7.6, 2.0]],
         "color": "accent", "width": 3}
      ],
      "notes": "Spoken notes for this slide."
    }
  ]
}
```

Element types:

| type | fields | notes |
|---|---|---|
| `image` | `path`, `box`, `fit` (`contain` default, or `stretch`), `name` | `contain` keeps the aspect ratio and centers the picture in the box. Raster files only: export SVG to PNG first |
| `text` | `text`, `box`, `style`, `size`, `color`, `bold`, `italic`, `align` (`left`, `center`, `right`), `valign` (`top`, `middle`, `bottom`), `name` | styles: `body`, `label` (bold), `caption` (4 pt smaller, muted), `callout` (2 pt smaller), `small` (6 pt smaller, muted) |
| `bubble` | same as `text`, plus `fill` (default `#F3F1EC`), `line`, `line_width` | rounded rectangle with the text inside; use for quotes and callouts. With no `line`, the bubble has no outline |
| `line` | `points` (list of `[x, y]`), `color`, `width`, `name` | native freeform polyline |

Inline markup inside any text: `**bold**`, `~~strikethrough~~`, `[[accent color]]`. Markup does not nest, has no escape character, and does not continue across a line break. Every newline starts a new paragraph. Every color field (`color`, `fill`, `line`, `background`, the theme colors, `title_color`, `title_bar.color`) accepts `#RRGGBB` or the theme names `text`, `muted`, `accent`. Set `theme.ea_font` when CJK text needs a different face from `font`.

A malformed spec stops the build with a message naming the slide and element (exit code 2) instead of writing a partial deck.

Per slide you may also set `background`, `title_bar`, `title_box` and `title_size`. The title is drawn last, so it sits above a title bar.

## Build, render, check

```bash
bash scripts/presentation-skill build-pptx deck/slides.json --render deck/verification/render
```

The build prints a warning for every text box whose estimated height exceeds its box, and for every slide without a title or notes. The estimate assumes an Arial-like width, counts CJK characters as full width and includes the font's own line height; it is still an estimate, so confirm on the render. `--render` converts through LibreOffice and pdftoppm into `slide-1.png`, `slide-2.png`, … (zero-padded to `slide-01.png` from ten slides on) plus `contact_sheet.png`. Look at every page: text inside its box, no label sitting on a busy part of a plate, captions near their figures.

## Google Slides handoff

- Pick fonts Google Slides already has (Arial, or Google Fonts such as Inter or Source Sans 3). Any other face gets substituted on import and the line breaks move.
- Upload the PPTX to Drive and open it with Google Slides, or upload with conversion to the Google Slides type. Speaker notes come across.
- LibreOffice and Google Slides lay text out slightly differently. After import, export the Google Slides file back to PDF and check it page by page before you send the link.
- Leave a little vertical slack in every text box. A box that fits exactly in LibreOffice may wrap one more line in Google Slides.
- Progressive builds become consecutive slides or several plates on one slide. Do not rely on animations surviving the import.
