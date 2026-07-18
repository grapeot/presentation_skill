from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from presentation_skill.asset_prep import prepare_asset


def _write_dark_icon(path: Path) -> None:
    image = Image.new("RGBA", (120, 80), (20, 24, 30, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle((35, 15, 85, 65), outline=(220, 180, 90, 255), width=6)
    image.save(path)


def test_prepare_asset_extracts_tints_and_tight_crops(tmp_path: Path):
    source = tmp_path / "source.png"
    output = tmp_path / "nested" / "output.png"
    _write_dark_icon(source)

    prepare_asset(
        source,
        output,
        target_color="#D6A24B",
        low=40,
        high=100,
        padding=3,
    )

    result = Image.open(output).convert("RGBA")
    assert result.width < 120
    assert result.height < 80
    assert result.getchannel("A").getbbox() is not None
    pixels = (
        result.get_flattened_data()
        if hasattr(result, "get_flattened_data")
        else result.getdata()
    )
    visible_colors = {pixel[:3] for pixel in pixels if pixel[3]}
    assert visible_colors == {(214, 162, 75)}


def test_prepare_asset_can_pad_to_square(tmp_path: Path):
    source = tmp_path / "source.png"
    output = tmp_path / "output.png"
    _write_dark_icon(source)

    prepare_asset(source, output, target_color="#D6A24B", crop="square")

    result = Image.open(output)
    assert result.width == result.height


def test_prepare_asset_rejects_invalid_thresholds(tmp_path: Path):
    source = tmp_path / "source.png"
    _write_dark_icon(source)

    with pytest.raises(ValueError, match="thresholds"):
        prepare_asset(source, tmp_path / "output.png", target_color="#D6A24B", low=100, high=40)
