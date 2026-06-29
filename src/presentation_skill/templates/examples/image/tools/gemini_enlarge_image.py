#!/usr/bin/env python3
"""
Command-line tool for upscaling images to 4K using Gemini 3.1 Flash Image Preview.
Takes a 1K image and regenerates it at 4K resolution while preserving content.
"""

import sys
import os
import argparse
import mimetypes
from typing import cast
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
script_dir = Path(__file__).parent
project_root = script_dir.parent
env_path = project_root / ".env"
load_dotenv(env_path)

def save_binary_file(file_name: str, data: bytes) -> None:
    """Save binary data to disk."""
    with open(file_name, "wb") as f:
        f.write(data)
    print(f"File saved to: {file_name}")

def enlarge(
    image_path: str,
    output_path: str,
) -> None:
    """Upscale the given image to 4K."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    if not Path(image_path).exists():
        print(f"Error: Input image not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    model = "gemini-3.1-flash-image-preview"

    # Read input image
    image_bytes = Path(image_path).expanduser().read_bytes()
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type:
        mime_type = "image/jpeg"

    # Construct Prompt
    prompt = "Upscale this image to 4K resolution. Maintain all details, text, and structure exactly. Do not add or remove elements. Just increase the resolution and sharpness."

    content = types.Content(
        role="user",
        parts=[
            types.Part.from_text(text=prompt),
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        ],
    )

    raw_config = {
        "response_modalities": ["IMAGE", "TEXT"],
        "image_config": {
            "aspect_ratio": "16:9",
            "image_size": "4K",
        },
    }
    generate_content_config = cast(types.GenerateContentConfigDict, cast(object, raw_config))

    print(f"Upscaling {image_path} to 4K...")
    
    try:
        # Using the generator loop as recommended for reliability
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=content,
            config=generate_content_config,
        ):
            candidate = chunk.candidates[0] if chunk.candidates else None
            content_out = candidate.content if candidate else None
            parts_out = content_out.parts if content_out and content_out.parts else []
            if not parts_out:
                continue

            for part in parts_out:
                inline_data = part.inline_data
                if inline_data and inline_data.data:
                    source_extension = mimetypes.guess_extension(inline_data.mime_type or "image/png") or ".png"
                    final_output_path = output_path
                    if not output_path.lower().endswith(source_extension.lower()):
                        final_output_path = str(Path(output_path).with_suffix(source_extension))
                    save_binary_file(final_output_path, inline_data.data)
                    return

    except Exception as e:
        print(f"Error during upscaling: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Upscale image to 4K")
    parser.add_argument("--input", "-i", required=True, help="Input image path")
    parser.add_argument("--output", "-o", required=True, help="Output image path")
    
    args = parser.parse_args()

    enlarge(args.input, args.output)

if __name__ == "__main__":
    main()
