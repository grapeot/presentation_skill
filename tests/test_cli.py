import subprocess
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]


def test_script_help_renders():
    result = subprocess.run(
        [str(ROOT / "scripts" / "presentation-skill"), "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert "Create starter artifacts" in result.stdout


def test_script_creates_image_starter(tmp_path: Path):
    out = tmp_path / "deck"
    subprocess.run(
        [
            str(ROOT / "scripts" / "presentation-skill"),
            "Launch narrative",
            "--mode",
            "image",
            "--output",
            str(out),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert (out / "deck_plan.md").exists()
    assert (out / "visual_guideline.md").exists()
    assert (out / "README.md").exists()
    assert (out / "examples" / "html" / "index.html").exists()


def test_script_creates_reveal_starter(tmp_path: Path):
    out = tmp_path / "deck"
    subprocess.run(
        [
            str(ROOT / "scripts" / "presentation-skill"),
            "Interactive demo",
            "--mode",
            "reveal",
            "--assets",
            "generated",
            "--output",
            str(out),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert (out / "deck_plan.md").exists()
    assert (out / "index.html").exists()
    assert (out / "js" / "deck.js").exists()
    assert (out / "js" / "slides" / "interactive-check.js").exists()
    assert (out / "imgs" / "cpu-blueprint.svg").exists()
    assert (out / "README.md").exists()
    assert (out / "examples" / "image" / "index.html").exists()
    assert (out / "examples" / "image" / "generated_slides" / "slide_01_0.jpg").exists()
    plan = (out / "deck_plan.md").read_text(encoding="utf-8")
    assert "Mode: reveal" in plan
    assert "Asset policy: generated" in plan


def test_html_mode_is_a_reveal_compatibility_alias(tmp_path: Path):
    out = tmp_path / "deck"
    subprocess.run(
        [
            str(ROOT / "scripts" / "presentation-skill"),
            "Legacy request",
            "--mode",
            "html",
            "--output",
            str(out),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert "Mode: reveal" in (out / "deck_plan.md").read_text(encoding="utf-8")


def test_script_prepares_transparent_asset(tmp_path: Path):
    source = tmp_path / "source.png"
    output = tmp_path / "output.png"
    image = Image.new("RGB", (80, 80), (20, 24, 30))
    ImageDraw.Draw(image).ellipse((20, 20, 60, 60), outline=(230, 200, 120), width=5)
    image.save(source)

    subprocess.run(
        [
            str(ROOT / "scripts" / "presentation-skill"),
            "prepare-asset",
            str(source),
            str(output),
            "--target-color",
            "#D6A24B",
            "--crop",
            "square",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    result = Image.open(output).convert("RGBA")
    assert result.width == result.height
    assert result.getchannel("A").getextrema() == (0, 255)
