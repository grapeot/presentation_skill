# Speaker Notes — Spoken-Delivery Contract

Read this file when creating, expanding, or substantially rewriting speaker notes. It is progressive-disclosure support for `skill_presentation.md`, not a second root skill.

## Goal

Write a direct-read script that sounds like a knowledgeable speaker addressing the room. The notes should be conversational without becoming casual, and authoritative without sounding like a textbook. Speaker notes add the reasoning, examples, transitions, and boundaries that do not fit on the slide.

---

## Acceptance Criteria

### 1. Spoken Language & Podium Voice
- **Natural Contractions**: Use natural contractions (e.g., `don't`, `it's`, `what's`, `we've`) naturally. Do not manufacture conversational tone with forced idioms or jokes.
- **Easy to Say**: Each sentence must be easy to say in one breath. Keep ordinary sentences between 12-20 words. **Hard gate**: no ordinary spoken sentence may exceed 22 words.
- **Single Payload**: One sentence may carry at most one main payload and one supporting clause. If it contains a condition, an exception, and a consequence, split it.
- **No Symmetrical Slogans**: Avoid repeated "not X, but Y" templates or formulaic slogans. They make a direct-read script sound AI-generated.

### 2. Narrative Flow & Transitions
- **Handoff Contract**: Slide transitions must behave like a physical handoff. Slide A's ending must explicitly raise the question or premise that Slide B's first sentence answers.
- **No Logical Detours**: When Slide B starts, it must address the handoff from Slide A immediately. Do not announce the new topic and then step backward into a detached history review.
- **Explain "Why Now"**: Introduce a concept only at the moment the audience needs it. Frame the intuitive meaning before the formal label.

### 3. Motivation, General-to-Specific, and Division
- **Motivation First**: Never list components, failures, or principles before the audience knows why they matter. Establish the shared parent problem first.
- **General-to-Specific Signposting (总分结构)**: Once the parent problem and motivation are clear, **do not jump into the list ad hoc**. You must write a clear, brief general-to-specific preview sentence (e.g., *"We need to screen workers on four practical fronts: A, B, C, and D. Let's look at each."*) before explaining the items.

---

## Podium Speech Translation Guide

Use this guide to translate written, textbook-style drafts into authentic spoken podium voice:

| Written / Textbook Style (Avoid) | Spoken / Podium Voice (Prefer) | Why? |
|---|---|---|
| "The model's default behavior is shaped by two distinct training forces. First is..." | "Now, you might ask: how does the model actually learn? It comes down to two forces. Let's look at..." | Engages the room with a rhetorical question; moves structure after motivation. |
| "Smarts are not enough. We evaluate workers across four distinct dimensions: reasoning quality, instruction following..." | "So, smarts aren't enough. We need to screen workers on four practical fronts: reasoning, rules, persistence, and tools. Let's look at each. First..." | Uses a transition cue (`So`), natural contractions, and a clear general-to-specific signpost. |
| "What form should the final artifact take? You might assume it is a PDF report. Human cognitive bandwidth is limited..." | "But what form should that artifact take? You might assume it's just another text report. But we can do better. Think about your morning..." | Bridges from the previous slide, uses personal reference (`your morning`), and creates visual stakes. |
| "The provenance is narrow. We are asking whether the artifact earned the confidence its presentation invites." | "This isn't a mission-impossible test. We're just checking whether the claims actually match the sources." | Translates abstract evaluation into a concrete, observable action. |

---

## Known Traps

| Trap | How it sounds | Correction |
|---|---|---|
| **Textbook Delivery** | "The default behavior is shaped by two forces..." | Explain the familiar effect first, then introduce the technical names only if they help. |
| **Audit-Report Voice** | "The provenance is narrow..." | Say the practical boundary: "We're just checking whether the claims match the sources." |
| **Plausible Narrative Override** | The notes tell a coherent story, but ignore the actual slide visual. | Rebuild from the locked slide claim, visual role, and chapter handoff. |
| **Silent Logical Jump** | One paragraph ends; the next starts a new topic without warning. | Recover the prior foothold: "So, for a stronger check...", "But there's a catch..." |
| **Signpost Wallpaper** | Every paragraph starts with the same `So`, `Now`, or `Key point is`. | Keep cues only at genuine logical turns and vary their form. |
| **Breathless Nesting** | A sentence stays under the word limit but nests condition + exception + consequence. | Split at the logical turn. Give the condition, action, and consequence their own beats. |
