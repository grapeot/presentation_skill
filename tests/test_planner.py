from pathlib import Path

import pytest

from presentation_skill import DeckMode, SlideSpec, build_deck_plan, choose_mode, validate_deck_plan
from presentation_skill.planner import write_html_mode_starter, write_image_mode_starter


def test_choose_mode_defaults_to_image():
    assert choose_mode("Create a product strategy deck") == DeckMode.IMAGE


def test_choose_mode_html_fallback_when_explicit():
    assert choose_mode("Create an HTML only interactive deck without image generation") == DeckMode.HTML


def test_validate_deck_plan_accepts_well_formed_plan():
    slides = [
        SlideSpec(1, "Opening", "The market changed faster than our planning loop.", "Timeline showing market speed versus planning cadence."),
        SlideSpec(2, "Decision", "We should fund the workflow layer before adding more dashboards.", "Two-column contrast between dashboard sprawl and workflow leverage."),
    ]
    assert validate_deck_plan(slides) == []


def test_validate_deck_plan_rejects_empty_plan():
    assert validate_deck_plan([]) == ["deck plan must contain at least one slide"]


def test_validate_deck_plan_rejects_duplicate_and_short_fields():
    slides = [
        SlideSpec(1, "", "short", "tiny"),
        SlideSpec(1, "Duplicate", "This claim is long enough to pass validation.", "This visual role is also long enough."),
    ]
    errors = validate_deck_plan(slides)
    assert "slide 1 is duplicated" in errors
    assert "slide 1 is missing a title" in errors
    assert "slide 1 claim is too short" in errors
    assert "slide 1 visual role is too short" in errors
    assert "slide 1 should be numbered 2" in errors


def test_build_deck_plan_renders_markdown():
    slides = [SlideSpec(1, "Opening", "The deck needs one visible claim per slide.", "A simple card showing claim, visual role, and note goal.")]
    markdown = build_deck_plan("Agentic presentations", slides, DeckMode.IMAGE)
    assert "# Presentation Deck Plan: Agentic presentations" in markdown
    assert "Mode: image" in markdown
    assert "### Slide 1: Opening" in markdown


def test_build_deck_plan_raises_on_invalid_plan():
    with pytest.raises(ValueError):
        build_deck_plan("Broken", [], DeckMode.IMAGE)


def test_write_image_mode_starter(tmp_path: Path):
    written = write_image_mode_starter(tmp_path / "deck", "Launch narrative")
    names = {path.name for path in written}
    assert names == {"deck_plan.md", "visual_direction.md", "slide_prompts.md", "speaker_notes.md"}
    assert (tmp_path / "deck" / "deck_plan.md").read_text(encoding="utf-8").startswith("# Presentation Deck Plan")


def test_write_html_mode_starter(tmp_path: Path):
    written = write_html_mode_starter(tmp_path / "deck", "Interactive demo")
    relative = {path.relative_to(tmp_path / "deck").as_posix() for path in written}
    assert relative == {"index.html", "slides/title.js", "deck_plan.md"}
    assert "Interactive demo" in (tmp_path / "deck" / "index.html").read_text(encoding="utf-8")
