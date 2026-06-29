from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


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
