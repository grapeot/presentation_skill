from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DeckMode(str, Enum):
    IMAGE = "image"
    REVEAL = "reveal"
    # Kept for callers that imported the pre-Reveal name directly.
    HTML = "html"


class AssetPolicy(str, Enum):
    NONE = "none"
    GENERATED = "generated"
    EXACT = "exact"
    MIXED = "mixed"


REVEAL_TRIGGERS = (
    "no image generation",
    "without image generation",
    "avoid image generation",
    "html only",
    "pure html",
    "editable html",
    "interactive deck",
    "reveal.js",
    "reveal deck",
    "exact copy",
    "exact text",
    "editable deck",
    "live data",
    "progressive interaction",
)

NO_GENERATED_ASSET_TRIGGERS = (
    "no image generation",
    "without image generation",
    "avoid image generation",
)

GENERATED_ASSET_TRIGGERS = (
    "generated icon",
    "generated icons",
    "ai-generated icon",
    "ai generated icon",
    "generated diagram",
    "generated illustration",
)

EXACT_ASSET_TRIGGERS = (
    "screenshot",
    "real chart",
    "exact chart",
    "logo",
    "qr code",
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
    if any(trigger in normalized for trigger in REVEAL_TRIGGERS):
        return DeckMode.REVEAL
    return DeckMode.IMAGE


def choose_asset_policy(user_request: str, mode: DeckMode | None = None) -> AssetPolicy:
    normalized = user_request.casefold()
    if any(trigger in normalized for trigger in NO_GENERATED_ASSET_TRIGGERS):
        return AssetPolicy.NONE

    has_generated = any(trigger in normalized for trigger in GENERATED_ASSET_TRIGGERS)
    has_exact = any(trigger in normalized for trigger in EXACT_ASSET_TRIGGERS)
    if has_generated and has_exact:
        return AssetPolicy.MIXED
    if has_generated:
        return AssetPolicy.GENERATED
    if has_exact:
        return AssetPolicy.EXACT

    selected_mode = mode or choose_mode(user_request)
    return AssetPolicy.GENERATED if selected_mode == DeckMode.IMAGE else AssetPolicy.MIXED


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


def build_deck_plan(
    topic: str,
    slides: list[SlideSpec],
    mode: DeckMode,
    asset_policy: AssetPolicy | None = None,
) -> str:
    errors = validate_deck_plan(slides)
    if errors:
        raise ValueError("invalid deck plan: " + "; ".join(errors))

    canonical_mode = DeckMode.REVEAL if mode == DeckMode.HTML else mode
    policy = asset_policy or (
        AssetPolicy.GENERATED if canonical_mode == DeckMode.IMAGE else AssetPolicy.MIXED
    )
    lines = [
        f"# Presentation Deck Plan: {topic}",
        "",
        f"Mode: {canonical_mode.value}",
        f"Asset policy: {policy.value}",
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
