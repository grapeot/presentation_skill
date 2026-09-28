from pathlib import Path

import pytest

from presentation_skill import (
    AssetPolicy,
    DeckMode,
    SlideSpec,
    build_deck_plan,
    choose_asset_policy,
    choose_mode,
    validate_deck_plan,
)
from presentation_skill.starter import write_html_mode_starter, write_image_mode_starter, write_reveal_mode_starter


def test_choose_mode_defaults_to_image():
    assert choose_mode("Create a product strategy deck") == DeckMode.IMAGE


def test_choose_mode_html_when_explicit():
    assert choose_mode("Create an HTML only interactive deck without image generation") == DeckMode.HTML


@pytest.mark.parametrize(
    ("user_request", "mode", "expected"),
    [
        ("HTML only, no image generation", DeckMode.HTML, AssetPolicy.NONE),
        ("Editable HTML with generated icons", DeckMode.HTML, AssetPolicy.GENERATED),
        ("Interactive deck with real screenshots", DeckMode.HTML, AssetPolicy.EXACT),
        ("Canvas deck with generated icons and screenshots", DeckMode.HTML, AssetPolicy.MIXED),
        ("Cinematic visual keynote", DeckMode.IMAGE, AssetPolicy.GENERATED),
    ],
)
def test_choose_asset_policy(user_request, mode, expected):
    assert choose_asset_policy(user_request, mode) == expected


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
    assert "Asset policy: generated" in markdown
    assert "### Slide 1: Opening" in markdown


def test_build_deck_plan_raises_on_invalid_plan():
    with pytest.raises(ValueError):
        build_deck_plan("Broken", [], DeckMode.IMAGE)


def test_write_image_mode_starter(tmp_path: Path):
    deck = tmp_path / "deck"
    written = write_image_mode_starter(deck, "Launch narrative")
    names = {path.name for path in written}
    assert "deck_plan.md" in names
    assert "README.md" in names
    assert "visual_guideline.md" in names
    assert "outline_visual.md" in names
    assert "custom.css" in names
    assert "slideModule.js" in names
    assert "generate_slides.py" in names
    assert (deck / "deck_plan.md").read_text(encoding="utf-8").startswith("# Presentation Deck Plan")
    assert (deck / "examples" / "html" / "index.html").exists()
    assert (deck / "examples" / "html" / "js" / "engine.js").exists()
    assert "Mode: image" in (deck / "deck_plan.md").read_text(encoding="utf-8")


def test_write_html_mode_starter(tmp_path: Path):
    deck = tmp_path / "deck"
    written = write_html_mode_starter(deck, "Interactive demo")
    names = {path.name for path in written}
    assert "deck_plan.md" in names
    assert "README.md" in names
    for required in [
        "index.html", "engine.js", "deck.js", "copy.js", "deck.css",
        "build_index.py", "copy_to_js.py", "shoot.py", "vendor.mjs", "package.json",
        "source_contract_template.md", "brief_template.md", "voice_contract_template.md",
        "writer_prompt_template.md", "visual_guideline.md", "cpu-blueprint.svg",
    ]:
        assert required in names, required
    # the canvas deck replaces the old per-slide module scaffold
    assert "slideModule.js" not in names
    assert "interactive-check.js" not in names
    index = (deck / "index.html").read_text(encoding="utf-8")
    assert "FRAMES:BEGIN" in index and 'id="world"' in index
    assert "cdn.jsdelivr.net" not in index  # the deck must run offline
    assert (deck / "examples" / "image" / "index.html").exists()
    assert (deck / "examples" / "image" / "generated_slides" / "slide_01_0.jpg").exists()
    plan = (deck / "deck_plan.md").read_text(encoding="utf-8")
    assert "Mode: html" in plan
    assert "Asset policy: mixed" in plan


def test_reveal_names_remain_compatibility_aliases(tmp_path: Path):
    written = write_reveal_mode_starter(tmp_path / "deck", "Legacy caller")
    assert any(path.name == "engine.js" for path in written)
    assert "Mode: html" in (tmp_path / "deck" / "deck_plan.md").read_text(encoding="utf-8")
    assert choose_mode("Build a reveal deck") == DeckMode.HTML
