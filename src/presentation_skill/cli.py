from __future__ import annotations

import argparse
from pathlib import Path

from .deck_plan import choose_mode
from .starter import write_html_mode_starter, write_image_mode_starter


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create starter artifacts for Presentation Skill decks")
    parser.add_argument("topic", help="Presentation topic")
    parser.add_argument("--request", default="", help="Original user request used to choose default mode")
    parser.add_argument("--mode", choices=["auto", "image", "html"], default="auto")
    parser.add_argument("--output", default="presentation_deck", help="Output directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    mode = choose_mode(args.request or args.topic).value if args.mode == "auto" else args.mode
    target = Path(args.output)
    if mode == "image":
        written = write_image_mode_starter(target, args.topic)
    else:
        written = write_html_mode_starter(target, args.topic)
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
