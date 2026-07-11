"""Export an image-mode deck to a distribution PDF with clickable links.

Compatibility contract
----------------------
The exporter only supports decks whose ``index.html`` is a pure image deck:
every ``<section>`` must consist of a ``data-background`` image that resolves
to a file under the deck directory, plus (optionally) one
``<aside class="notes">`` block. Any other visible content inside a section —
extra tags, text nodes, inline overlays — makes the deck incompatible, because
the PDF would silently drop it. In that case the export **fails loudly**
instead of producing a lossy PDF.

Clickable links come from the optional ``<script id="overlay-data">`` JSON
block (see ``docs/clickable_overlays.md``). Each hotzone rect is expressed in
fractions of the slide; the exporter embeds PDF link annotations at the same
rects, with the same default padding the HTML overlay layer applies, so the
PDF and the HTML deck click identically.

Page images are embedded losslessly (``img2pdf``), matching the quality of the
rendered slides; no browser printing is involved.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_PAD = 0.015

_SECTION_RE = re.compile(r"<section\b([^>]*)>(.*?)</section>", re.S | re.I)
_BG_RE = re.compile(r"data-background=\"([^\"]+)\"")
_ID_RE = re.compile(r"id=\"([^\"]+)\"")
_ASIDE_RE = re.compile(r"<aside\s+class=\"notes\"[^>]*>.*?</aside>", re.S | re.I)
_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
_OVERLAY_RE = re.compile(
    r"<script\s+id=\"overlay-data\"\s+type=\"application/json\">\s*(\{.*?\})\s*</script>",
    re.S,
)


class CompatibilityError(RuntimeError):
    """Deck cannot be exported without losing content."""

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__(
            "Deck is not compatible with image-PDF export:\n"
            + "\n".join(f"  - {p}" for p in problems)
        )


@dataclass
class SectionInfo:
    index: int  # 0-based page index
    section_id: str
    background: Path


@dataclass
class CompatReport:
    ok: bool
    problems: list[str] = field(default_factory=list)
    sections: list[SectionInfo] = field(default_factory=list)
    overlays: dict = field(default_factory=dict)


def _load_index(deck_dir: Path) -> str:
    index = deck_dir / "index.html"
    if not index.is_file():
        raise FileNotFoundError(f"{index} not found — not a deck directory?")
    return index.read_text(encoding="utf-8")


def check_compatibility(deck_dir: Path) -> CompatReport:
    """Validate that the deck is background-image + notes (+ overlays) only."""
    deck_dir = Path(deck_dir)
    html = _load_index(deck_dir)
    problems: list[str] = []
    sections: list[SectionInfo] = []

    matches = _SECTION_RE.findall(html)
    if not matches:
        problems.append("no <section> elements found in index.html")

    for i, (attrs, inner) in enumerate(matches):
        label = f"section {i + 1}"
        id_m = _ID_RE.search(attrs)
        section_id = id_m.group(1) if id_m else ""
        if section_id:
            label += f" (id={section_id})"

        bg_m = _BG_RE.search(attrs)
        if not bg_m:
            problems.append(f"{label}: no data-background image")
            continue
        bg_path = deck_dir / bg_m.group(1)
        if not bg_path.is_file():
            problems.append(f"{label}: background image not found: {bg_m.group(1)}")

        residual = _ASIDE_RE.sub("", inner)
        residual = _COMMENT_RE.sub("", residual).strip()
        if residual:
            snippet = re.sub(r"\s+", " ", residual)[:80]
            problems.append(
                f"{label}: contains content beyond background + notes "
                f"(would be lost in PDF): {snippet!r}"
            )

        sections.append(SectionInfo(index=i, section_id=section_id, background=bg_path))

    overlays: dict = {}
    overlay_m = _OVERLAY_RE.search(html)
    if overlay_m:
        try:
            overlays = json.loads(overlay_m.group(1))
        except json.JSONDecodeError as exc:
            problems.append(f"overlay-data block is not valid JSON: {exc}")
            overlays = {}
        section_ids = {s.section_id for s in sections}
        for sid, items in overlays.items():
            if sid not in section_ids:
                problems.append(f"overlay-data references unknown section id {sid!r}")
                continue
            for j, item in enumerate(items):
                rect = item.get("rect")
                href = item.get("href", "")
                if (
                    not isinstance(rect, list)
                    or len(rect) != 4
                    or not all(isinstance(v, (int, float)) and 0 <= v <= 1 for v in rect)
                    or not (rect[0] < rect[2] and rect[1] < rect[3])
                ):
                    problems.append(f"{sid} hotzone {j}: invalid rect {rect!r}")
                if not href.startswith(("http://", "https://")):
                    problems.append(f"{sid} hotzone {j}: href must be http(s), got {href!r}")

    return CompatReport(ok=not problems, problems=problems, sections=sections, overlays=overlays)


def export_pdf(
    deck_dir: Path,
    output: Path | None = None,
    pad: float = DEFAULT_PAD,
) -> tuple[Path, int, int]:
    """Build the PDF. Returns (output_path, page_count, link_count).

    Raises :class:`CompatibilityError` if the deck cannot be exported
    losslessly, so callers never receive a silently degraded PDF.
    """
    deck_dir = Path(deck_dir)
    report = check_compatibility(deck_dir)
    if not report.ok:
        raise CompatibilityError(report.problems)

    try:
        import img2pdf  # type: ignore
        from pypdf import PdfReader, PdfWriter  # type: ignore
        from pypdf.generic import (  # type: ignore
            ArrayObject,
            DictionaryObject,
            FloatObject,
            NameObject,
            NumberObject,
            TextStringObject,
        )
    except ImportError as exc:  # pragma: no cover - environment-specific
        raise RuntimeError(
            "PDF export requires the optional dependencies: "
            "pip install 'presentation-skill[pdf]' (img2pdf + pypdf)"
        ) from exc

    import io

    pdf_bytes = img2pdf.convert([str(s.background) for s in report.sections])
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()
    writer.append(reader)

    id_to_page = {s.section_id: s.index for s in report.sections if s.section_id}
    n_links = 0
    for sid, items in report.overlays.items():
        page = writer.pages[id_to_page[sid]]
        w = float(page.mediabox.width)
        h = float(page.mediabox.height)
        for item in items:
            x1f, y1f, x2f, y2f = item["rect"]
            item_pad = float(item.get("pad", pad))
            rect = ArrayObject(
                [
                    FloatObject(round((x1f - item_pad) * w, 2)),
                    FloatObject(round(h - (y2f + item_pad) * h, 2)),
                    FloatObject(round((x2f + item_pad) * w, 2)),
                    FloatObject(round(h - (y1f - item_pad) * h, 2)),
                ]
            )
            annot = DictionaryObject(
                {
                    NameObject("/Type"): NameObject("/Annot"),
                    NameObject("/Subtype"): NameObject("/Link"),
                    NameObject("/Rect"): rect,
                    NameObject("/Border"): ArrayObject(
                        [NumberObject(0), NumberObject(0), NumberObject(0)]
                    ),
                    NameObject("/A"): DictionaryObject(
                        {
                            NameObject("/S"): NameObject("/URI"),
                            NameObject("/URI"): TextStringObject(item["href"]),
                        }
                    ),
                }
            )
            ref = writer._add_object(annot)
            if "/Annots" in page:
                page[NameObject("/Annots")].append(ref)
            else:
                page[NameObject("/Annots")] = ArrayObject([ref])
            n_links += 1

    if output is None:
        output = deck_dir / f"{deck_dir.resolve().name}.pdf"
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "wb") as fh:
        writer.write(fh)
    return output, len(writer.pages), n_links
