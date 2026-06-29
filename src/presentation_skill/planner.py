from __future__ import annotations

import os
import shutil
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


def _template_root() -> Path:
    return Path(__file__).parent / "templates"


def _copy_template_dir(src: Path, dest: Path) -> None:
    if not src.exists():
        return
    dest.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.name == "__pycache__":
            continue
        d_item = dest / item.name
        if item.is_dir():
            _copy_template_dir(item, d_item)
        else:
            shutil.copy2(item, d_item)


def _get_all_files(target_dir: Path) -> list[Path]:
    written: list[Path] = []
    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for file in files:
            written.append(Path(root) / file)
    return written


def _write_deck_plan(target_dir: Path, topic: str, mode: DeckMode) -> None:
    (target_dir / "deck_plan.md").write_text(
        f"# Presentation Deck Plan: {topic}\n\nMode: {mode.value}\n\n## Slide Plan\n\n",
        encoding="utf-8",
    )


def _write_deck_readme(target_dir: Path) -> None:
    bootstrap_readme = _template_root() / "bootstrap" / "DECK_README.md"
    if bootstrap_readme.exists():
        shutil.copy2(bootstrap_readme, target_dir / "README.md")


def write_image_mode_starter(target_dir: Path, topic: str) -> list[Path]:
    template_root = _template_root()
    target_dir.mkdir(parents=True, exist_ok=True)

    _copy_template_dir(template_root / "common", target_dir)
    _copy_template_dir(template_root / "examples" / "image", target_dir)
    _copy_template_dir(template_root / "examples" / "html", target_dir / "examples" / "html")

    _write_deck_plan(target_dir, topic, DeckMode.IMAGE)
    _write_deck_readme(target_dir)

    return _get_all_files(target_dir)


def write_html_mode_starter(target_dir: Path, topic: str) -> list[Path]:
    template_root = _template_root()
    target_dir.mkdir(parents=True, exist_ok=True)

    _copy_template_dir(template_root / "common", target_dir)
    _copy_template_dir(template_root / "examples" / "html", target_dir)
    _copy_template_dir(template_root / "examples" / "image", target_dir / "examples" / "image")

    _write_deck_plan(target_dir, topic, DeckMode.HTML)
    _write_deck_readme(target_dir)

    return _get_all_files(target_dir)
