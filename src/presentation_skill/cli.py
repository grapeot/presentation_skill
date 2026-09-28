from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .deck_plan import AssetPolicy, DeckMode, choose_asset_policy, choose_mode
from .starter import write_html_mode_starter, write_image_mode_starter

_SUBCOMMANDS = {"init", "export-pdf", "prepare-asset"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="presentation-skill",
        description="Presentation Skill helpers: scaffold decks, prepare assets, export decks to PDF",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Create starter artifacts for a new deck")
    init.add_argument("topic", help="Presentation topic")
    init.add_argument("--request", default="", help="Original user request used to choose default mode")
    init.add_argument("--mode", choices=["auto", "image", "html", "reveal"], default="auto")
    init.add_argument(
        "--assets",
        choices=["auto", "none", "generated", "exact", "mixed"],
        default="auto",
        help="Local asset policy, independent of slide rendering mode",
    )
    init.add_argument("--output", default="presentation_deck", help="Output directory")

    export = sub.add_parser(
        "export-pdf",
        help="Export a deck to PDF: image decks from their slide images, HTML (canvas) decks through headless Chromium",
    )
    export.add_argument("deck_dir", help="Deck directory containing index.html")
    export.add_argument(
        "--output",
        default=None,
        help="Output PDF path (default: image deck <deck_dir>/<name>.pdf; "
        "HTML deck <deck_dir>/verification/handout.pdf or handout_with_notes.pdf)",
    )
    export.add_argument(
        "--check-only",
        action="store_true",
        help="Run the checks and exit without writing a PDF",
    )
    export.add_argument(
        "--mode",
        choices=["auto", "image", "html", "canvas"],
        default="auto",
        help="Exporter to use; auto picks html when the deck has js/engine.js and window.DECK "
        "(canvas is an alias of html)",
    )
    export.add_argument(
        "--with-notes",
        action="store_true",
        help="HTML decks: follow every slide page with a page of its speaker notes",
    )
    export.add_argument(
        "--image-quality",
        type=int,
        default=85,
        help="HTML decks: JPEG quality for large embedded images, 1-100 (0 keeps them lossless; default 85)",
    )
    export.add_argument(
        "--image-scale",
        type=float,
        default=2.0,
        help="HTML decks: cap <img> resolution at this multiple of the displayed size (0 keeps originals; default 2)",
    )
    export.add_argument(
        "--no-contact-sheet",
        action="store_true",
        help="HTML decks: skip the contact sheet written next to the PDF",
    )

    asset = sub.add_parser(
        "prepare-asset",
        help="Convert a generated icon or diagram into a tinted transparent PNG",
    )
    asset.add_argument("input", help="Source image")
    asset.add_argument("output", help="Output PNG")
    asset.add_argument("--target-color", required=True, help="Output foreground color, e.g. #D6A24B")
    asset.add_argument("--background", choices=["dark", "light"], default="dark")
    asset.add_argument("--low", type=int, default=40, help="Background-side luminance threshold")
    asset.add_argument("--high", type=int, default=100, help="Foreground-side luminance threshold")
    asset.add_argument("--padding", type=int, default=24)
    asset.add_argument("--crop", choices=["tight", "square", "none"], default="tight")

    return parser


def _run_init(args: argparse.Namespace) -> int:
    request = args.request or args.topic
    if args.mode == "auto":
        mode = choose_mode(request)
    else:
        mode = DeckMode.HTML if args.mode == "reveal" else DeckMode(args.mode)
    policy = choose_asset_policy(request, mode) if args.assets == "auto" else AssetPolicy(args.assets)
    target = Path(args.output)
    if mode == DeckMode.IMAGE:
        written = write_image_mode_starter(target, args.topic, policy)
    else:
        written = write_html_mode_starter(target, args.topic, policy)
    for path in written:
        print(path)
    return 0


def _run_prepare_asset(args: argparse.Namespace) -> int:
    from .asset_prep import prepare_asset

    output = prepare_asset(
        Path(args.input),
        Path(args.output),
        target_color=args.target_color,
        background=args.background,
        low=args.low,
        high=args.high,
        padding=args.padding,
        crop=args.crop,
    )
    print(output)
    return 0


def resolve_export_mode(mode: str, deck_dir: Path) -> str:
    """'image' or 'html' for the export-pdf subcommand."""
    from .export_html_pdf import is_canvas_deck

    if mode == "canvas":
        return "html"
    if mode == "auto":
        return "html" if is_canvas_deck(deck_dir) else "image"
    return mode


def _run_export_pdf(args: argparse.Namespace) -> int:
    deck_dir = Path(args.deck_dir)
    mode = resolve_export_mode(args.mode, deck_dir)
    if mode == "html":
        return _run_export_html_pdf(args, deck_dir)
    if args.with_notes:
        print("--with-notes applies to HTML (canvas) decks; image-deck PDFs carry no notes pages")
        return 2

    from .export_pdf import CompatibilityError, check_compatibility, export_pdf

    if args.check_only:
        report = check_compatibility(deck_dir)
        if report.ok:
            n_zones = sum(len(v) for v in report.overlays.values())
            print(f"compatible: {len(report.sections)} slides, {n_zones} link hotzones")
            return 0
        for problem in report.problems:
            print(f"INCOMPATIBLE: {problem}")
        return 2

    try:
        output, pages, links = export_pdf(deck_dir, Path(args.output) if args.output else None)
    except CompatibilityError as exc:
        print(exc)
        return 2
    print(f"{output} ({pages} pages, {links} links)")
    return 0


def _run_export_html_pdf(args: argparse.Namespace, deck_dir: Path) -> int:
    from .export_html_pdf import HtmlExportError, MissingDependencyError, export_canvas_pdf

    try:
        result = export_canvas_pdf(
            deck_dir,
            Path(args.output) if args.output else None,
            with_notes=args.with_notes,
            contact_sheet=not args.no_contact_sheet,
            check_only=args.check_only,
            image_quality=args.image_quality,
            image_scale=args.image_scale,
        )
    except MissingDependencyError as exc:
        print(exc)
        return 3
    except (HtmlExportError, ValueError) as exc:
        print(exc)
        return 2
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    if args.check_only:
        print(f"ok: {result.slides} slides, print states checked, no errors, no external requests, no missing slots")
        return 0
    size_mb = result.output.stat().st_size / 1e6
    print(f"{result.output} ({result.pages} pages: {result.slides} slides"
          + (f" + {result.slides} notes pages" if args.with_notes else "")
          + f"; {size_mb:.1f} MB, {result.merged_bytes / 1e6:.1f} MB before image dedupe/compression)")
    if any(result.flattened.values()):
        print("re-drawn as images for PDF viewers: "
              + ", ".join(f"{v} {k}" for k, v in result.flattened.items() if v))
    for sheet in result.contact_sheets:
        print(f"contact sheet: {sheet}")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    # Backward compatibility: `presentation-skill "Topic" --mode image` predates
    # subcommands and must keep working for existing scripts and skills.
    if argv and argv[0] not in _SUBCOMMANDS and argv[0] not in ("-h", "--help"):
        argv = ["init", *argv]

    args = build_parser().parse_args(argv)
    if args.command == "init":
        return _run_init(args)
    if args.command == "prepare-asset":
        return _run_prepare_asset(args)
    return _run_export_pdf(args)


if __name__ == "__main__":
    raise SystemExit(main())
