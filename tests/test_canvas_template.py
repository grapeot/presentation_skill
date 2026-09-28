"""Offline checks on the canvas (Reveal mode) template: the builder regenerates frames, every data-in/slot
references a slide in the table, and copy conversion round-trips."""
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "src" / "presentation_skill" / "templates" / "examples" / "reveal"


def _copy(tmp_path: Path) -> Path:
    deck = tmp_path / "deck"
    shutil.copytree(TEMPLATE, deck)
    return deck


def test_builder_regenerates_frames(tmp_path: Path):
    deck = _copy(tmp_path)
    subprocess.run([sys.executable, "tools/build_index.py"], cwd=deck, check=True, capture_output=True)
    html = (deck / "index.html").read_text(encoding="utf-8")
    assert html.count('class="frame"') == 5
    assert html.count("FRAMES:BEGIN") == 1 and html.count("FRAMES:END") == 1


def test_markup_references_known_slides(tmp_path: Path):
    deck = _copy(tmp_path)
    ids = set(re.findall(r'S\("([a-z_0-9]+)"', (deck / "js" / "deck.js").read_text(encoding="utf-8")))
    html = (deck / "index.html").read_text(encoding="utf-8")
    frames = set(re.findall(r'<div class="frame" id="([a-z_0-9]+)"', html))
    assert frames == ids
    refs = re.findall(r'data-(?:in|out|count|bar|follow)="([a-z_0-9]+)\.\d+"', html)
    refs += [t.split("@")[1].split(".")[0] for s in re.findall(r'data-state="([^"]+)"', html) for t in s.split()]
    assert set(refs) - {"end"} <= ids


def test_copy_round_trip(tmp_path: Path):
    deck = _copy(tmp_path)
    subprocess.run([sys.executable, "tools/copy_to_js.py"], cwd=deck, check=True, capture_output=True)
    js = (deck / "js" / "copy.js").read_text(encoding="utf-8")
    html = (deck / "index.html").read_text(encoding="utf-8")
    for slot in re.findall(r'data-slot="([a-z_0-9]+)\.([a-z_0-9]+)"', html):
        assert f'"{slot[1]}"' in js, slot
