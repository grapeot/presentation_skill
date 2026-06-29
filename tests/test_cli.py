import subprocess
from pathlib import Path


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


def test_script_creates_html_starter(tmp_path: Path):
    out = tmp_path / "deck"
    subprocess.run(
        [
            str(ROOT / "scripts" / "presentation-skill"),
            "Interactive demo",
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
    assert (out / "deck_plan.md").exists()
    assert (out / "index.html").exists()
    assert (out / "js" / "slides" / "title.js").exists()
    assert (out / "README.md").exists()
    assert (out / "examples" / "image" / "index.html").exists()
    assert (out / "examples" / "image" / "generated_slides" / "slide_01_0.jpg").exists()
