from __future__ import annotations

import os
import shutil
from pathlib import Path

from .deck_plan import DeckMode


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
