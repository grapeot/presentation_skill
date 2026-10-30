from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from .deck_plan import AssetPolicy, DeckMode


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


def _write_deck_plan(
    target_dir: Path,
    topic: str,
    mode: DeckMode,
    asset_policy: AssetPolicy,
) -> None:
    (target_dir / "deck_plan.md").write_text(
        f"# Presentation Deck Plan: {topic}\n\n"
        f"Mode: {mode.value}\n"
        f"Asset policy: {asset_policy.value}\n\n"
        "## Slide Plan\n\n",
        encoding="utf-8",
    )


def _write_deck_readme(target_dir: Path) -> None:
    bootstrap_readme = _template_root() / "bootstrap" / "DECK_README.md"
    if bootstrap_readme.exists():
        shutil.copy2(bootstrap_readme, target_dir / "README.md")


def write_image_mode_starter(
    target_dir: Path,
    topic: str,
    asset_policy: AssetPolicy = AssetPolicy.GENERATED,
) -> list[Path]:
    template_root = _template_root()
    target_dir.mkdir(parents=True, exist_ok=True)

    _copy_template_dir(template_root / "common", target_dir)
    _copy_template_dir(template_root / "examples" / "image", target_dir)
    _copy_template_dir(template_root / "examples" / "html", target_dir / "examples" / "html")

    _write_deck_plan(target_dir, topic, DeckMode.IMAGE, asset_policy)
    _write_deck_readme(target_dir)

    return _get_all_files(target_dir)


def write_html_mode_starter(
    target_dir: Path,
    topic: str,
    asset_policy: AssetPolicy = AssetPolicy.MIXED,
) -> list[Path]:
    template_root = _template_root()
    target_dir.mkdir(parents=True, exist_ok=True)

    # The canvas deck brings its own server-free tooling (tools/shoot.py serves itself); only requirements are shared.
    _copy_template_dir(template_root / "examples" / "html", target_dir)
    shutil.copy2(template_root / "common" / "requirements.txt", target_dir / "requirements.txt")
    shutil.copy2(template_root / "common" / "start-server.py", target_dir / "start-server.py")
    _copy_template_dir(template_root / "examples" / "image", target_dir / "examples" / "image")

    _write_deck_plan(target_dir, topic, DeckMode.HTML, asset_policy)
    _write_deck_readme(target_dir)

    return _get_all_files(target_dir)


def write_reveal_mode_starter(
    target_dir: Path,
    topic: str,
    asset_policy: AssetPolicy = AssetPolicy.MIXED,
) -> list[Path]:
    """Compatibility wrapper for the former "reveal" mode name."""
    return write_html_mode_starter(target_dir, topic, asset_policy)


_PPTX_README = """# Editable PPTX deck

Edit `slides.json`, put image plates in `plates/`, then build and look at the render:

    presentation-skill build-pptx slides.json --render verification/render

Every word on a slide stays a native text box. Spec format and the Google Slides
handoff checklist are in the skill's `pptx_decks.md`.
"""


def write_pptx_mode_starter(
    target_dir: Path,
    topic: str,
    asset_policy: AssetPolicy = AssetPolicy.GENERATED,
) -> list[Path]:
    """Scaffold an editable-PPTX deck: a one-slide spec to copy from, a plates folder and a README."""
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "plates").mkdir(exist_ok=True)
    spec = {
        "theme": {"font": "Arial", "title_size": 30, "body_size": 20},
        "slides": [{
            "title": f"{topic}: the one claim this slide makes",
            "elements": [
                {"type": "bubble", "box": [0.8, 1.6, 6.0, 1.6], "line": "muted", "valign": "middle",
                 "text": "A quote or example the speaker can point at.\n[[Speaker, date]]"},
                {"type": "text", "style": "label", "box": [7.3, 1.6, 5.3, 1.2],
                 "text": "**Label**\nOne sentence that supports the claim."},
                {"type": "text", "style": "caption", "box": [0.8, 6.4, 11.8, 0.6],
                 "text": "Caption: what the figure shows and why it matters here."},
            ],
            "notes": "Spoken notes: what the speaker says on this slide.",
        }],
    }
    (target_dir / "slides.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
    (target_dir / "README.md").write_text(_PPTX_README, encoding="utf-8")
    _write_deck_plan(target_dir, topic, DeckMode.PPTX, asset_policy)
    return _get_all_files(target_dir)
