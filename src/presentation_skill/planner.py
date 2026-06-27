from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class DeckMode(str, Enum):
    IMAGE = "image"
    HTML = "html"


HTML_FALLBACK_TRIGGERS = (
    "no image generation",
    "without image generation",
    "avoid image generation",
    "html only",
    "pure html",
    "editable html",
    "interactive deck",
)


@dataclass(frozen=True)
class SlideSpec:
    number: int
    title: str
    claim: str
    visual_role: str
    notes_goal: str = ""


def choose_mode(user_request: str) -> DeckMode:
    normalized = user_request.casefold()
    if any(trigger in normalized for trigger in HTML_FALLBACK_TRIGGERS):
        return DeckMode.HTML
    return DeckMode.IMAGE


def validate_deck_plan(slides: list[SlideSpec]) -> list[str]:
    errors: list[str] = []
    if not slides:
        return ["deck plan must contain at least one slide"]

    seen_numbers: set[int] = set()
    for expected, slide in enumerate(slides, start=1):
        if slide.number in seen_numbers:
            errors.append(f"slide {slide.number} is duplicated")
        seen_numbers.add(slide.number)
        if slide.number != expected:
            errors.append(f"slide {slide.number} should be numbered {expected}")
        if not slide.title.strip():
            errors.append(f"slide {slide.number} is missing a title")
        if len(slide.claim.strip()) < 12:
            errors.append(f"slide {slide.number} claim is too short")
        if len(slide.visual_role.strip()) < 12:
            errors.append(f"slide {slide.number} visual role is too short")
    return errors


def build_deck_plan(topic: str, slides: list[SlideSpec], mode: DeckMode) -> str:
    errors = validate_deck_plan(slides)
    if errors:
        raise ValueError("invalid deck plan: " + "; ".join(errors))

    lines = [
        f"# Presentation Deck Plan: {topic}",
        "",
        f"Mode: {mode.value}",
        "",
        "## Slide Plan",
        "",
    ]
    for slide in slides:
        lines.extend(
            [
                f"### Slide {slide.number}: {slide.title}",
                f"Claim: {slide.claim}",
                f"Visual role: {slide.visual_role}",
                f"Speaker notes goal: {slide.notes_goal or 'Support the claim with concrete spoken context.'}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def write_image_mode_starter(target_dir: Path, topic: str) -> list[Path]:
    target_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "deck_plan.md": f"# Presentation Deck Plan: {topic}\n\nMode: image\n\n## Slide Plan\n\n",
        "visual_direction.md": "# Visual Direction\n\nDefine lighting, material, color semantics, typography, and what must stay consistent across slides.\n",
        "slide_prompts.md": "# Slide Prompts\n\nUse one section per slide. Include exact readable text and the visual role of each element.\n",
        "speaker_notes.md": "# Speaker Notes\n\nWrite notes that can be read aloud and that add context not already visible on the slide.\n",
    }
    written: list[Path] = []
    for name, content in files.items():
        path = target_dir / name
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def write_html_mode_starter(target_dir: Path, topic: str) -> list[Path]:
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "slides").mkdir(exist_ok=True)
    files = {
        "index.html": HTML_INDEX_TEMPLATE.replace("{{TOPIC}}", topic),
        "slides/title.js": HTML_TITLE_TEMPLATE.replace("{{TOPIC}}", topic),
        "deck_plan.md": f"# Presentation Deck Plan: {topic}\n\nMode: html\n\n## Slide Plan\n\n",
    }
    written: list[Path] = []
    for name, content in files.items():
        path = target_dir / name
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


HTML_INDEX_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{TOPIC}}</title>
  <style>
    body { margin: 0; font-family: system-ui, sans-serif; background: #0f172a; color: #f8fafc; }
    main { width: min(1080px, 92vw); margin: 8vh auto; }
    section { min-height: 70vh; display: grid; place-items: center; border: 1px solid #334155; border-radius: 24px; padding: 48px; }
    h1 { font-size: clamp(36px, 7vw, 84px); line-height: 1; }
  </style>
</head>
<body>
  <main id="deck"></main>
  <script type="module">
    import { html } from './slides/title.js';
    document.getElementById('deck').innerHTML = html;
  </script>
</body>
</html>
"""


HTML_TITLE_TEMPLATE = """export const html = `
<section>
  <div>
    <p>Presentation</p>
    <h1>{{TOPIC}}</h1>
    <aside class="notes">Open with the problem this deck helps the audience decide.</aside>
  </div>
</section>
`;
"""
