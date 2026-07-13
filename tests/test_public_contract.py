from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_exactly_one_root_skill():
    skills = sorted((ROOT / "skills").glob("*.md"))
    assert [skill.name for skill in skills] == [
        "reference.md",
        "skill_presentation.md",
        "speaker_notes.md",
    ]
    root_skills = [
        skill.name
        for skill in skills
        if skill.read_text(encoding="utf-8").startswith("---\n")
    ]
    assert root_skills == ["skill_presentation.md"]


def test_required_docs_exist():
    for rel in ["docs/prd.md", "docs/rfc.md", "docs/test.md", "docs/working.md"]:
        assert (ROOT / rel).exists(), rel


def test_no_legacy_large_artifact_names():
    forbidden = {"Holistic Generation of Slide Decks.pdf", "styles", "generated_slides"}
    present = {path.name for path in ROOT.iterdir()}
    assert forbidden.isdisjoint(present)


def test_readme_points_to_root_skill():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "skills/skill_presentation.md" in readme
    assert "https://github.com/grapeot/presentation_skill" in readme
