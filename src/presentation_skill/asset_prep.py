from __future__ import annotations

from pathlib import Path


def _parse_hex_color(value: str) -> tuple[int, int, int]:
    normalized = value.removeprefix("#")
    if len(normalized) != 6:
        raise ValueError("target color must use six hex digits, e.g. #D6A24B")
    try:
        return tuple(int(normalized[index : index + 2], 16) for index in (0, 2, 4))  # type: ignore[return-value]
    except ValueError as exc:
        raise ValueError("target color must use six hex digits, e.g. #D6A24B") from exc


def prepare_asset(
    input_path: Path,
    output_path: Path,
    *,
    target_color: str,
    background: str = "dark",
    low: int = 40,
    high: int = 100,
    padding: int = 24,
    crop: str = "tight",
) -> Path:
    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - exercised only without the optional extra
        raise RuntimeError(
            "prepare-asset requires Pillow; install with `uv pip install -e '.[assets]'`"
        ) from exc

    if background not in {"dark", "light"}:
        raise ValueError("background must be 'dark' or 'light'")
    if crop not in {"tight", "square", "none"}:
        raise ValueError("crop must be 'tight', 'square', or 'none'")
    if not 0 <= low < high <= 255:
        raise ValueError("thresholds must satisfy 0 <= low < high <= 255")
    if padding < 0:
        raise ValueError("padding must be non-negative")

    color = _parse_hex_color(target_color)
    source = Image.open(input_path).convert("RGBA")
    gray = source.convert("L")
    source_alpha = source.getchannel("A")

    def map_alpha(pair: tuple[int, int]) -> int:
        luminance, existing_alpha = pair
        position = (luminance - low) / (high - low)
        if background == "light":
            position = 1.0 - position
        mapped = max(0.0, min(1.0, position))
        return round(mapped * existing_alpha)

    gray_values = (
        gray.get_flattened_data() if hasattr(gray, "get_flattened_data") else gray.getdata()
    )
    alpha_values = (
        source_alpha.get_flattened_data()
        if hasattr(source_alpha, "get_flattened_data")
        else source_alpha.getdata()
    )
    alpha = Image.new("L", source.size)
    alpha.putdata([map_alpha(pair) for pair in zip(gray_values, alpha_values)])
    result = Image.new("RGBA", source.size, (*color, 0))
    result.putalpha(alpha)

    if crop != "none":
        bbox = alpha.getbbox()
        if bbox is None:
            raise ValueError("no foreground remained after alpha extraction")
        left, top, right, bottom = bbox
        result = result.crop(
            (
                max(0, left - padding),
                max(0, top - padding),
                min(source.width, right + padding),
                min(source.height, bottom + padding),
            )
        )
        if crop == "square" and result.width != result.height:
            side = max(result.size)
            square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
            square.alpha_composite(result, ((side - result.width) // 2, (side - result.height) // 2))
            result = square

    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.save(output_path, format="PNG")
    return output_path
