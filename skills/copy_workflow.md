# Copy Workflow: Writer Drafts, Builder Checks

Read this before writing on-screen copy or speaker notes for a Reveal (canvas) deck.

## Division of labour

| Role | Who | Owns |
|---|---|---|
| Editor and builder | the main agent | thesis, slide list, visual system, motion, code, fact checks, final acceptance |
| Writer | a separate writing model in a fresh session; the reference setup uses Antigravity CLI (`agy --print`, `gemini-3.8-flash-high`) | all on-screen copy and the spoken script |
| Critic | a fresh sub-agent that sees only screenshots and a rubric | ranked visual problems ([critic_review.md](critic_review.md)) |

A strong coding agent is better at motion, layout and following constraints; a strong writing model is better at
prose. Give the prose to the writer. **If no separate writer is available, the builder writes the copy itself**
against the same contracts and keeps the same drift checks. Record which path was used in `validation.md`.

## The writer's packet

Put these in a minimal scratch directory and pass absolute paths. Templates are in the scaffold under `copy/`.

- `source_contract.md`: every fact, number, date and quote the copy may use, each with its source and its
  qualifiers; the speaker's positions with their exact boundaries; stories marked as witnessed or illustrative.
- `deck_brief.md`: audience, opening question, thesis, closing line; per slide the id, minutes, what the picture
  does, and the copy slots with word limits. FIXED slots carry exact text.
- `voice_contract.md`: the spoken register and the on-screen register.
- `writer_prompt.md`: the task. The output is one `copy.md` with a fixed per-slide schema so `tools/copy_to_js.py`
  can parse it.

Run the writer in a fresh session (for Antigravity: `--new-project`, an explicit `--print-timeout`, the process's
working directory in the scratch dir). Then verify the file actually landed where it should and has every slide
section. A non-zero or "error" status can come from the writer's closing summary overflowing its output limit
while the file itself is complete; check the file, not only the status.

Word budget: about 130 spoken words per minute. `tools/copy_to_js.py` prints the total and the estimated duration.

## The builder's drift check

Read every slot and every paragraph against the source contract. The writer is fluent but does not follow
instructions reliably. These are the drifts that actually occurred, in order of how often:

- **Semantic slot drift.** A slot filled with the opposite of what it must carry. For example, a "problem that
  persists" slot filled with the patch that expires ("fitting facts into a limited window", "standardising the
  interface").
- **Illustration turned into testimony.** A hypothetical ("for example, someone might…") rewritten as "I once
  watched…". Invented details added to a real story (a message count, a season, a job title).
- **Causal claims added to data.** A chart of what changed gained a story of why it changed.
- **Qualifier loss or inflation.** "May get faster" became "gets faster"; "once the field settles" became "after
  decades".
- **Wrong small facts.** Time of day, what a course reading actually says, how an assessment actually works, what
  happened in a cited example.
- **Audience misfit.** References the audience does not share: a school, app or company from another context.
- **Idioms and hype** despite the voice contract.

Fix each drift surgically: restore the contract's wording and leave the voice alone. When a whole passage needs
new reasoning (for example, resolving an apparent contradiction the owner raised), send a small targeted packet
back to the writer rather than rewriting it yourself. Every fix goes into `validation.md`, as does every
builder-authored on-screen string (structural labels, a claim added after a critic round).

## Audit every choice against the audience

Before building, and again whenever the owner asks "why is this here?", check each example, name and reference
against one question: does this make these specific listeners understand faster or believe more? A reference
that survives only because it was in the source material ("we used it in the last talk") gets replaced with one
the audience already lives with. Verify replacements from primary sources: a localized example that is
technically wrong, such as a payment flow that does not actually retry on the client, is worse than the original.
