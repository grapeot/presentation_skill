# Copy Workflow: Writer Drafts, Builder Checks

Before you begin drafting any on-screen copy or writing speaker notes for a Reveal (canvas) deck, take a few minutes to read through this workflow guide.

## Division of labour

| Role | Who | Owns |
|---|---|---|
| Editor and builder | This is the main agent | The core thesis, slide list, visual system, motion design, code, fact checking, and final acceptance |
| Writer | A dedicated writing model running in a clean session; our reference setup uses Antigravity CLI (`agy --print`, `gemini-3.8-flash-high`) | Drafting all the on-screen copy as well as the spoken script |
| Critic | A fresh sub-agent provided strictly with screenshots and an evaluation rubric | Finding and ranking visual issues ([critic_review.md](critic_review.md)) |

In practice, a capable coding agent is much better at motion, layout, and following constraints, whereas a dedicated writing model produces far more natural prose. That's why you want to hand off the prose to the writer whenever possible. **If no separate writer is available, the builder writes the copy itself** against the same contracts and keeps the same drift checks in place. Whichever path you take, be sure to record it in `validation.md`.

## The writer's packet

To set up the writer properly, place the following files into a minimal scratch directory and pass them around using absolute paths. If you need starter templates, you can find them in the scaffold right under `copy/`.

- `source_contract.md`: This file lays out every fact, number, date, and quote that the copy is allowed to use, along with its specific source and qualifiers. It also spells out the speaker's positions with their exact boundaries, and explicitly marks whether stories were firsthand witnessed experiences or illustrative hypotheticals.
- `deck_brief.md`: Here you define the target audience, the opening question, the overarching thesis, and the closing line. For each individual slide, specify its id, allocated minutes, what the visual accomplishes, and the specific copy slots along with their word limits. Note that any FIXED slots carry exact text that cannot be changed.
- `voice_contract.md`: This sets the tone for both the spoken register and the on-screen register.
- `writer_prompt.md`: This defines the actual task. It instructs the writer to produce a single `copy.md` file that adheres to a fixed per-slide schema so `tools/copy_to_js.py` can parse it cleanly.

When you run the writer, always do so in a fresh session. If you are using Antigravity, pass `--new-project`, provide an explicit `--print-timeout`, and set the process's working directory right in the scratch dir. Once the run finishes, take a moment to verify that the file actually landed where it should and that it contains every single slide section. Keep in mind that seeing a non-zero exit code or an "error" status can happen simply because the writer's closing summary overflowed its output limit while the file itself is entirely complete, so always check the file itself, not only the status.

As for your word budget, plan for about 130 spoken words per minute. When you run `tools/copy_to_js.py`, it will print out the total word count alongside an estimated speaking duration.

## The builder's drift check

Once you have the draft, read through every single slot and every paragraph against your source contract. The writer model produces very fluent text, but it does not follow instructions reliably. In practice, here are the exact kinds of drift that actually occurred on past runs, ordered from most frequent to least frequent:

- **Semantic slot drift.** This happens when a slot gets filled with the exact opposite of what it must carry. For example, a slot reserved for a "problem that persists" might end up filled with a temporary patch that expires, like "fitting facts into a limited window" or "standardising the interface".
- **Illustration turned into testimony.** This occurs when a hypothetical scenario ("for example, someone might…") gets rewritten as personal testimony ("I once watched…"). You will also see invented details added to a real story, such as a fabricated message count, a season, or a job title.
- **Causal claims added to data.** A chart that simply displayed what changed suddenly acquires an invented story explaining why it changed.
- **Qualifier loss or inflation.** Careful nuance gets lost: a cautious phrase like "may get faster" turns into "gets faster", or a measured caveat like "once the field settles" gets inflated into "after decades".
- **Wrong small facts.** Minor factual details get scrambled, such as the time of day, what a course reading actually says, how an assessment actually works, or what actually happened in a cited example.
- **Audience misfit.** The copy introduces references that your specific audience does not share, like bringing up a school, app, or company from a completely different context.
- **Idioms and hype.** Unwanted buzzwords, clichés, and hype sneak into the text despite what the voice contract specified.

When you find these drifts, fix each one surgically: restore the contract's wording and leave the voice alone. When an entire passage requires new reasoning—for instance, when resolving an apparent contradiction raised by the deck owner—send a small, targeted packet back to the writer rather than trying to rewrite the passage yourself. Every fix must be recorded in `validation.md`, and that includes every builder-authored on-screen string, such as structural labels or any new claim added after a critic round.

## Audit every choice against the audience

Before you begin building, and again whenever the owner pauses to ask "why is this here?", take a moment to check each example, name, and reference against a single question: does this make these specific listeners understand faster or believe more? If a reference survives only because it happened to be in the original source material ("we used it in the last talk"), that reference must be replaced with one the audience already lives with. Verify your replacements from primary sources: introducing a localized example that is technically wrong, such as describing a payment flow that does not actually retry on the client, is far worse than leaving the original in place.
