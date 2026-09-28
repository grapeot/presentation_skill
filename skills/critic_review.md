# Critic Review

"Premium" and "clear" cannot be verified by the agent that built the deck. Run an independent critic on every
revision round before the owner sees it. On the first canvas deck, two rounds moved every rubric score from
5–7 to about 7, and the owner did not have to spend attention on problems the critic had already caught.

## The loop

1. Freeze a shots directory for the round: `python3 tools/shoot.py --out verification/roundN`. Never re-shoot
   into a directory a critic is reading.
2. Write `verification/critic/rubric.md` once per deck: the target feel in the owner's words, the visual register,
   6–8 criteria, and the genre's kitsch traps.
3. Start a fresh sub-agent with the prompt below. It sees screenshots and the rubric only: no code, no reasoning.
4. Fix the top problems. Prefer changes to scale, composition, material and type over adding elements.
5. On the next round, give the critic its previous review; it marks each item fixed, partly fixed or not fixed.

## Prompt template

> You are an art director reviewing an animated lecture deck rendered as screenshots of every click. Find what
> stops it from looking {target feel}; do not praise.
> Read first: {rubric path}{; your previous review: path}.
> Frames: contact sheets {paths}; full-resolution frames {pattern}. Open at least {list} at full resolution and
> crop around anything small. Story beats: {one line per slide}.
> Judge at the size it will be seen: {delivery, e.g. projected and shared over Zoom, about 1/3 scale}.
> Output (≤ 700 words), also saved to {path}: (1) a score out of 10 per criterion, each with one sentence of
> evidence naming a step and a location; (2) the top 5–7 problems ranked by cost, each with the steps, what a viewer
> perceives, and one concrete change to the picture; (3) up to three things to protect; (4) if a previous review is
> given, re-check each item. Describe the picture only: no process or tool suggestions, and do not read source code.

## What critics kept finding

Check for these before the first round:

- **A claim set as an eyebrow.** A 16 px grey caps label carrying the actual claim reads as metadata.
- **A foreign widget.** A dark UI panel in a paper-and-ink deck reads as SaaS. Reprint it in the deck's material.
- **An equal-weight card grid at the climax.** Give the cards material, and let the click change them physically.
- **Dead space.** Blank half-frames next to crowded ones, orphaned footnotes far below a grid.
- **Diagrams as thin vector boxes.** Draw tension as tension (springs along edges), put the choice inside, and
  caption with a claim rather than the labels again.
- **Closing lines in two voices.** Pick one voice (for example ink serif at about 38 px) for every closing line.
- **Italics, decorative numerals and a third accent colour everywhere**, so nothing lands.
- **Data labels that mislead.** Old and new values sitting in the same place; a different metric set louder than
  the chart it sits beside.
