# Critic Review

Abstract goals like making a deck feel "premium" and "clear" simply cannot be verified by the agent that built it. That's why you want to run an independent critic on every revision round before the owner ever sees it. In practice, on our very first canvas deck, running two rounds moved every rubric score from the 5–7 range up to about 7, and the owner did not have to spend attention on problems the critic had already caught.

## The loop

1. Freeze a shots directory for the round using `python3 tools/shoot.py --out verification/roundN`. Never re-shoot into a directory a critic is reading.
2. Write `verification/critic/rubric.md` once per deck: lay out the target feel in the owner's words, the visual register, 6–8 criteria, and the genre's kitsch traps.
3. Start a fresh sub-agent with the prompt below. It sees screenshots and the rubric only: no code, no reasoning.
4. Address the top problems. As a rule, prefer changes to scale, composition, material and type over adding elements.
5. On the next round, give the critic its previous review so it can mark each item fixed, partly fixed or not fixed.

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

It saves a lot of time if you check for these before the first round:

- **A claim set as an eyebrow.** When a 16 px grey caps label carries the actual claim, it reads as metadata rather than the main point.
- **A foreign widget.** A dark UI panel in a paper-and-ink deck reads as SaaS. Reprint it in the deck's material instead.
- **An equal-weight card grid at the climax.** Make sure to give the cards material, and let the click change them physically so the moment lands.
- **Dead space.** Watch out for blank half-frames next to crowded ones, or orphaned footnotes floating far below a grid.
- **Diagrams as thin vector boxes.** Draw tension as tension (such as using springs along edges), put the choice inside, and caption with a claim rather than the labels again.
- **Closing lines in two voices.** Pick one voice (for example ink serif at about 38 px) for every closing line across the deck.
- **Italics, decorative numerals and a third accent colour everywhere**, so nothing lands. When everything tries to look special, none of the emphasis works.
- **Data labels that mislead.** Watch out for old and new values sitting in the same place, or a different metric set louder than the chart it sits beside.
