"""Tests for the image-deck generator template (`tools/generate_slides.py`).

The template is copied into deck scaffolds and normally imports the deck's
runtime backends (`google-genai`, `openai`, `python-dotenv`). Those modules are
stubbed here so the pure dispatch logic stays testable offline. The template is
loaded by path so the tests exercise the exact shipped file.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
IMAGE_TEMPLATE = ROOT / "src/presentation_skill/templates/examples/image"
GENERATOR = IMAGE_TEMPLATE / "tools/generate_slides.py"
STUB_MODULES = (
    "tools",
    "tools.gemini_generate_image",
    "tools.openai_generate_image",
)


@pytest.fixture(scope="module")
def generator():
    package = types.ModuleType("tools")
    package.__path__ = [str(IMAGE_TEMPLATE / "tools")]
    sys.modules["tools"] = package
    for name in ("gemini_generate_image", "openai_generate_image"):
        module = types.ModuleType(f"tools.{name}")
        module.generate = lambda **kwargs: None  # type: ignore[attr-defined]
        sys.modules[f"tools.{name}"] = module

    spec = importlib.util.spec_from_file_location("deck_generate_slides", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    yield module

    for name in STUB_MODULES:
        sys.modules.pop(name, None)


def test_variant_defaults_follow_size(generator):
    assert generator._resolve_variant("gpt", "1K", "auto") == "gpt-image-2.5-flare"
    assert generator._resolve_variant("gpt", "2K", "auto") == "gpt-image-2.5-sunburst"
    assert generator._resolve_variant("gpt", "4K", "auto") == "gpt-image-2.5-sunburst"
    assert generator._resolve_variant("gemini", "1K", "auto") is None


def test_variant_override_wins_over_size(generator):
    assert generator._resolve_variant("gpt", "1K", "sunburst") == "gpt-image-2.5-sunburst"
    assert generator._resolve_variant("gpt", "4K", "flare") == "gpt-image-2.5-flare"


def test_parser_defaults(generator):
    args = generator.build_parser().parse_args([])
    assert args.model == "gpt"
    assert args.variant == "auto"
    assert args.quality is None
    assert args.size is None


def test_parser_accepts_all_2_5_quality_tiers(generator):
    for tier in ("low", "medium", "high", "xhigh", "max", "auto"):
        assert generator.build_parser().parse_args(["--quality", tier]).quality == tier
    with pytest.raises(SystemExit):
        generator.build_parser().parse_args(["--quality", "ultra"])


def test_default_quality_is_auto(generator):
    args = generator.build_parser().parse_args([])
    model, size, quality, _workers = generator._resolve_defaults(args)
    assert (model, size, quality) == ("gpt", "4K", "auto")


def test_size_override_flows_into_variant(generator):
    args = generator.build_parser().parse_args(["--size", "1K"])
    _model, size, _quality, _workers = generator._resolve_defaults(args)
    assert generator._resolve_variant("gpt", size, args.variant) == "gpt-image-2.5-flare"


def test_generate_slide_passes_all_assets_and_model_id(generator, tmp_path, monkeypatch):
    first = tmp_path / "a.png"
    second = tmp_path / "b.png"
    first.write_bytes(b"a")
    second.write_bytes(b"b")

    captured: dict = {}
    monkeypatch.setattr(
        generator.openai_generate_image,
        "generate",
        lambda **kwargs: captured.update(kwargs),
    )

    slide = {"number": 1, "content": "one claim", "asset_paths": [str(first), str(second)]}
    generator.generate_slide(
        slide,
        "guideline",
        tmp_path,
        tmp_path,
        model="gpt",
        image_size="1K",
        quality="auto",
        openai_model_id="gpt-image-2.5-flare",
    )

    assert captured["model_id"] == "gpt-image-2.5-flare"
    assert captured["quality"] == "auto"
    assert captured["image_paths"] == [str(first), str(second)]
    assert not list(tmp_path.glob("stacked_assets_*"))
